import datetime

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import memcache

import os
import jinja2

# START Global variables

DEFAULT_DROPZONE_NAME = "No Dropzone"  # deprecated
DEFAULT_DROPZONE_ID = 5659313586569216
DEFAULT_DROPZONE_STATUS = "No Status"  # deprecated
DROPZONE_STATUS = ["Open", "Closed"]
OPEN = 0
CLOSED = 1
LOAD_STATUS = ["Waiting","In the air", "On hold", "Landed"] # - waiting, flying, hold, landed
LOAD_COLOURS = [("bg-primary", "text-white"), ("bg-success", "text-white"), ("bg-warning", "text-white"),
                ("bg-secondary", "text-white")]
WAITING = 0
FLYING = 1
HOLD = 2
LANDED = 3
DEFAULT_LOAD_ID = 0
REGISTRATION_STATUS = ["Current", "Not Current"]
REGISTRATION_COLOURS = [("badge-success", ""), ("badge-warning", "")]
CURRENT = 0
NOT_CURRENT = 1
USER_ROLES = ["Admin", "Manifest", "Sales", "View Only"]  # - admin, manifest, sales, view
ROLE_COLOURS = [("badge-primary", ""), ("badge-success", ""), ("badge-info", ""),
                ("badge-secondary", "")]
ADMIN = 0
MANIFEST = 1
SALES = 2
VIEW = 3
DEFAULT_KIOSK_NUMBER_OF_COLUMNS = 4
DEFAULT_SLICE_SIZE = 4
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

# [END Global variables]


class Dropzone(ndb.Model):
    name = ndb.StringProperty()
    default_load_time = ndb.IntegerProperty()
    default_load_number = ndb.IntegerProperty()
    default_slot_number = ndb.IntegerProperty()
    status = ndb.IntegerProperty()
    tag = ndb.StringProperty()
    kiosk_cols = ndb.IntegerProperty()
    kiosk_rows = ndb.IntegerProperty()

    @classmethod
    def _get_by_id(cls, id, parent=None, **ctx_options):
        dropzone = memcache.get(str(id))
        if dropzone is not None :
            return dropzone
        else :
            dropzone = cls.get_by_id(id, parent, ctx_options)
            memcache.add(str(id),dropzone)
            return dropzone

    def _put(self, **ctx_options):
        memcache.delete(str(self.key.id()))
        return self.put(self, ctx_options)


class Load(ndb.Model):
    number = ndb.IntegerProperty()
    slots = ndb.IntegerProperty()      # total slots on the load
    preceded_by = ndb.IntegerProperty()
    time = ndb.TimeProperty()
    date = ndb.DateProperty(auto_now_add=True)
    status = ndb.IntegerProperty()
    dropzone = ndb.IntegerProperty()

    @classmethod
    def get_loads (cls, dropzone_key) :
        return cls.query(Load.date == datetime.date.today(),Load.dropzone == dropzone_key).order(Load.number)

    @classmethod
    def add_load(cls, dropzone_key):
        dropzone = Dropzone.get_by_id(dropzone_key)
        ls = LoadStructure(dropzone_key)
        loads = ls.loads
        last = len(loads) - 1
        time_increment = datetime.timedelta(minutes=dropzone.defaultloadtime)
        if last >= 0:
            load = Load(number=loads[last].number + 1,
                        slots=dropzone.defaultloadnumber,
                        precededby=loads[last].key.id(),
                        status=WAITING,
                        time=NextLoadTimeDz(loads[last], dropzone),
                        dropzone=dropzone_key
                        )
        else:
            load = Load(
                number=1,
                slots=dropzone.defaultloadnumber,
                precededby=-1,
                status=WAITING,
                time=(datetime.datetime.now() + time_increment).time(),
                dropzone=dropzone_key
            )
        return load


class Manifest(ndb.Model):
    load = ndb.IntegerProperty()  # The key for the load that this manifest applies to
    jumper = ndb.IntegerProperty() # The key for jumper this applies to

    @classmethod
    def get_by_load(cls, load_key) :
        return cls.query(Manifest.load == load_key)

    @classmethod
    def delete_manifest(cls, load_key, jumper_key):
        manifest = Manifest.query(Manifest.load == load_key, Manifest.jumper == jumper_key).fetch()
        return manifest[0].key.delete()


class User(ndb.Model):
    name = ndb.StringProperty()
    dropzone = ndb.IntegerProperty()
    role = ndb.IntegerProperty()

    @classmethod
    def _get_by_id(cls, id, parent=None, **ctx_options):
        user = memcache.get(str(id))
        if user is not None :
            return user
        else :
            user = cls.get_by_id(id, parent, ctx_options)
            memcache.add(str(id),user)
            return user

    def _put(self, **ctx_options):
        memcache.delete(str(self.key.id()))
        self.put(ctx_options)

    @classmethod
    def get_user (cls, name) :
        q = cls.query(User.name == name).fetch(keys_only=True)
        if q:
            id = q[0].id()
            user = memcache.get(str(id))
            if user is not None:
                return user
            else:
                return cls.get_by_id(id)

    @classmethod
    def get_by_dropzone(cls, dropzone_key):
        return cls.query(User.dropzone == dropzone_key).order(User.name)


class Registration(ndb.Model) :
    jumper = ndb.IntegerProperty()
    dropzone = ndb.IntegerProperty()
    waiver = ndb.DateProperty()
    reserve = ndb.DateProperty()
    current = ndb.IntegerProperty()

    @classmethod
    def get_by_dropzone (cls, dropzone) :
        return cls.query(Registration.dropzone == dropzone)

    @classmethod
    def get_by_jumper(cls, dropzone_key, jumper_key):
        return cls.query(Registration.dropzone == dropzone_key, Registration.jumper == jumper_key)

    @classmethod
    def get_all_by_jumper(cls, jumper_key):
        return cls.query(Registration.jumper == jumper_key)


class Sale(ndb.Model) :
    jumper = ndb.IntegerProperty()
    dropzone = ndb.IntegerProperty()
    jumps_remaining = ndb.IntegerProperty()
    package = ndb.IntegerProperty()

    @classmethod
    def getSales(cls, dropzone_key, jumper_key):
        return cls.query(Sale.jumper == jumper_key, Sale.dropzone == dropzone_key).order(Sale.package)


class SalesPackage(ndb.Model):
    name = ndb.StringProperty()
    dropzone = ndb.IntegerProperty()
    description = ndb.StringProperty()
    size = ndb.IntegerProperty()

    @classmethod
    def get_by_dropzone(cls, dropzone_key):
        return cls.query(SalesPackage.dropzone == dropzone_key).order(SalesPackage.name)


class Jumper(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    google_id = ndb.StringProperty()

    @classmethod
    def get_by_email(cls, email):
        return cls.query(Jumper.email == email)

    @classmethod
    def get_by_gid(cls, gid):
        return cls.query(Jumper.google_id == gid)


# Creates a LoadStructure - loads and manifest - for dropzone for today using the copy in memcache if exists.
class LoadStructure:
    loads = []
    slot_mega = {}
    load_struct = ()
    dropzone_key = DEFAULT_DROPZONE_ID

    def __init__(self, dropzone_key):
        key = str(dropzone_key) + "ls"
        self.load_struct = memcache.get(key)
        self.dropzone_key = dropzone_key
        if self.load_struct is None :
            self.load_struct = LoadStructure.refresh(dropzone_key)
        self.loads = self.load_struct[0]
        self.slot_mega = self.load_struct[1]

    # refreshes the memcache from the permanent store
    @classmethod
    def refresh(cls,dropzone_key):
        loads = Load.get_loads(dropzone_key).fetch()
        manifests = Manifest.query().fetch()
        slot_mega = {}
        for load in loads:
            slots = []
            for manifest in manifests:
                if manifest.load == load.key.id():
                    slots.append(Jumper.get_by_id(manifest.jumper))
            slot_mega.update({load.key.id(): slots})
        load_struct = (loads, slot_mega)
        key = str(dropzone_key) + "ls"
        memcache.add(key,load_struct)
        return load_struct

    #creates a dict showing the number of freeslots for each load in the LoadStructure
    def freeslots(self):
        frees = {}
        slot_number = Dropzone.get_by_id(self.dropzone_key).default_slot_number
        if slot_number:
            for load in self.loads:
                free = slot_number - len(self.slot_mega[load.key.id()])
                frees.update({load.key.id(): free})
        return frees

    # retimes the load Structure using the preceded_by parameter
    def retime_chain(self):
        flag = True
        while flag:
            flag = False
            load = self.loads[0]
            for next_load in self.loads:
                if next_load.preceded_by == load.key.id():
                    if next_load.status in [WAITING, HOLD]:
                        next_load.time = NextLoadTimeDz(load, self.dropzone_key)
                    load = next_load
                    load.put()
                    flag = True
                    break
        return self


class JumperStructure (type) :
    @classmethod
    def get(mcs, dropzone_key) :
        jumpers = memcache.get(str(dropzone_key) + "js")
        if jumpers is not None :
            return jumpers
        else :
            return JumperStructure.refresh(dropzone_key)

    @classmethod
    def refresh(mcs, dropzone_key) :
        registrations = Registration.get_by_dropzone(dropzone_key).fetch()
        jumpers = []
        for registration in registrations:
            jumper_key = registration.jumper
            jumpers.append((Jumper.get_by_id(jumper_key), registration))
        memcache.add(str(dropzone_key) + "js",jumpers)
        return jumpers


def UserStatus (uri) :
    # set up the user context and links for the navbar
    user = users.get_current_user()
    if user:
        url = users.create_logout_url(uri)
        url_linktext = 'Logout'
    else:
        url = users.create_login_url(uri)
        url_linktext = 'Login'
    return {'user':user, 'url':url, 'url_linktext':url_linktext}


# Deletes a load and all associated Manifests
def DeleteLoad(load, dropzone_key):
    ls = LoadStructure(dropzone_key)
    manifests = Manifest.get_by_load(load.key.id())
    for next_load in ls.loads:
        if next_load.preceded_by == load.key.id():
            next_load.preceded_by = load.precededby
            next_load.put()
    load.key.delete()
    for manifest in manifests :
        manifest.key.delete()

    # Have to refresh loads to reset the memcache and to avoid re-inserting the deleted load
    loads = LoadStructure.refresh(dropzone_key)[0]
    # Retime all loads
    if len(loads) != 0:
        ls.retimechain()
    for manifest in manifests :
        manifest.key.delete()
    return


# FUNCTION that calculates the time object for a load based on the last load and the required interval - can also be used
# to calculate the new time object for a load based on the current status of the load and the required time increment
def NextLoadTime(previous_load, time_increment):
    return (datetime.datetime.combine(datetime.date(1, 1, 1), previous_load.time) + time_increment).time()


# Function to calculate NextLoadTime based upon DZ
def NextLoadTimeDz(previous_load, dropzone):
    return NextLoadTime(previous_load, datetime.timedelta(minutes=dropzone.defaultloadtime))




