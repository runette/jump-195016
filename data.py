import datetime

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import memcache

import os
import jinja2

# START Global variables

DEFAULT_DROPZONE_NAME = "No Dropzone"  # deprecated
DEFAULT_DROPZONE_ID = 0
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
    def get_by_id(cls, id, parent=None, **ctx_options):
        if id == DEFAULT_DROPZONE_ID or id == None:
            dropzone = Dropzone(
                id=0,
                name="default",
                default_load_time=0,
                default_load_number=0,
                default_slot_number=0,
                status=CLOSED,
                tag="",
                kiosk_cols=1,
                kiosk_rows=1,
            )
        else:
            dropzone = memcache.get(str(id))
            if dropzone is None :
                dropzone = cls._get_by_id(id, parent, **ctx_options)
                memcache.add(str(id),dropzone)
        return dropzone

    def put(self, **ctx_options):
        if self.has_complete_key():
            memcache.delete(str(self.key.id()))
        return self._put( **ctx_options)


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

    def put(self, **ctx_options):
        ret = self._put( **ctx_options)
        if self.has_complete_key():
            ls = LoadStructure(self.dropzone)
            ls.refresh()
        return ret


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
    def get_user (cls, name) :
        q = cls.query(User.name == name).fetch(keys_only=True)
        if q:
            id = q[0].id()
            user = memcache.get(str(id))
            if user is not None:
                return user
            else:
                return cls.get_by_id(id)
        else:
            user = User(
                name=name,
                dropzone=DEFAULT_DROPZONE_ID,
            )
            user.put()
            return user

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

    def put(self, **ctx_options):
        ret = self._put( **ctx_options)
        if self.has_complete_key():
            js = JumperStructure(self.dropzone)
            js.refresh()
        return ret

    def delete(self):
        self.key.delete()
        js = JumperStructure(self.dropzone)
        js.refresh()
        return


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
        ls = memcache.get(key)
        self.dropzone_key = dropzone_key
        if ls is None :
            self.refresh()
        else:
            self.load_struct = ls
            self.loads = self.load_struct[0]
            self.slot_mega = self.load_struct[1]
        return

    # refreshes the memcache from the permanent store
    def refresh(self):
        loads = Load.get_loads(self.dropzone_key).fetch()
        manifests = Manifest.query().fetch()
        slot_mega = {}
        for load in loads:
            slots = []
            for manifest in manifests:
                if manifest.load == load.key.id():
                    slots.append(Jumper.get_by_id(manifest.jumper))
            slot_mega.update({load.key.id(): slots})
        self.load_struct = (loads, slot_mega)
        self.loads = self.load_struct[0]
        self.slot_mega = self.load_struct[1]
        self.save()
        return

    def save(self):
        key = str(self.dropzone_key) + "ls"
        client = memcache.Client()
        while True:  # Retry loop
            content = client.gets(key)
            if content is None:
                memcache.set(key, self.load_struct,time=300)
                break
            if client.cas(key, self.load_struct, time=300):
                break
        return

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
        dropzone=Dropzone.get_by_id(self.dropzone_key)
        flag = True
        load = self.loads[0]
        if len(self.loads) !=0 :
            while flag:
                flag = False
                for next_load in self.loads:
                    if next_load.preceded_by == load.key.id():
                        if next_load.status in [WAITING, HOLD]:
                            next_load.time = NextLoadTimeDz(load, dropzone)
                        load = next_load
                        load._put()
                        flag = True
                        break
        self.refresh()
        return self

    def add_load(self):
        dropzone = Dropzone.get_by_id(self.dropzone_key)
        loads = self.loads
        last = len(loads) - 1
        time_increment = datetime.timedelta(minutes=dropzone.default_load_time)
        if last >= 0:
            load = Load(number=loads[last].number + 1,
                        slots=dropzone.default_load_number,
                        preceded_by=loads[last].key.id(),
                        status=WAITING,
                        time=NextLoadTimeDz(loads[last], dropzone),
                        dropzone=self.dropzone_key
                        )
        else:
            load = Load(
                number=1,
                slots=dropzone.default_load_number,
                preceded_by=-1,
                status=WAITING,
                time=(datetime.datetime.now() + time_increment).time(),
                dropzone=self.dropzone_key
            )
        load.put()
        self.loads.append(load)
        self.slot_mega.update({load.key.id(): []})
        self.load_struct = (self.loads, self.slot_mega)
        self.save()
        return

    # Deletes a load and all associated Manifests
    def delete_load(self, load):
        manifests = Manifest.get_by_load(load.key.id())
        for next_load in self.loads:
            if next_load.preceded_by == load.key.id():
                next_load.preceded_by = load.preceded_by
                next_load.put()
        load.key.delete()
        for manifest in manifests:
            manifest.key.delete()
        # Have to refresh loads to reset the memcache and to avoid re-inserting the deleted load
        self.refresh()
        # Retime all loads
        return

    def add_manifest(self,load_key, jumper_key):
        manifest = Manifest(
            load=load_key,
            jumper=jumper_key
        )
        manifest.put()
        slots = self.slot_mega[load_key]
        slots.append(Jumper.get_by_id(manifest.jumper))
        self.save()
        return


class JumperStructure () :
    jumpers = []
    dropzone_key=0

    def __init__(self, dropzone_key) :
        self.dropzone_key=dropzone_key
        jumpers = memcache.get(str(dropzone_key) + "js")
        if jumpers is not None :
            self.jumpers =  jumpers
        else :
            self.refresh()
        return

    def refresh(self) :
        registrations = Registration.get_by_dropzone(self.dropzone_key).fetch()
        self.jumpers = []
        for registration in registrations:
            jumper_key = registration.jumper
            self.jumpers.append((Jumper.get_by_id(jumper_key), registration))
        self.save()
        return

    def save(self):
        key = str(self.dropzone_key) + "js"
        client = memcache.Client()
        while True:  # Retry loop
            content = client.gets(key)
            if content is None:
                memcache.set(key, self.jumpers,time=300)
                break
            if client.cas(key, self.jumpers, time=300):
                break
        return


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




# FUNCTION that calculates the time object for a load based on the last load and the required interval - can also be used
# to calculate the new time object for a load based on the current status of the load and the required time increment
def NextLoadTime(previous_load, time_increment):
    return (datetime.datetime.combine(datetime.date(1, 1, 1), previous_load.time) + time_increment).time()


# Function to calculate NextLoadTime based upon DZ
def NextLoadTimeDz(previous_load, dropzone):
    return NextLoadTime(previous_load, datetime.timedelta(minutes=dropzone.default_load_time))




