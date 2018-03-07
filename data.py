import datetime

from google.appengine.api import users
from google.appengine.ext import ndb

import os
import jinja2

#[START Global variables]

DEFAULT_DROPZONE_NAME = "No Dropzone"  # deprecated
DEFAULT_DROPZONE_ID = 5659313586569216
DEFAULT_DROPZONE_STATUS = "No Status"  # deprecated
DROPZONE_STATUS = ["Open", "Closed"]
OPEN = 0
CLOSED = 1
LOAD_STATUS = ["Waiting","In the air", "On hold", "Landed"] # - waiting, flying, hold, landed
WAITING = 0
FLYING = 1
HOLD = 2
LANDED = 3
DEFAULT_LOAD_ID = 0
REGISTRATION_STATUS = ["Yes", "No"]
CURRENT = 0
NOT_CURRENT = 1
USER_ROLES = ["Admin", "Manifest", "Sales", "View Only"]  # - admin, manifest, sales, view
ROLE_COLOURS = [("bg-primary", "text-white"), ("bg-success", "text-white"), ("bg-info", "text-white"),
                ("bg-secondary", "text-white")]
ADMIN = 0
MANIFEST = 1
SALES = 2
VIEW = 3
KIOSK_NUMBER_OF_COLUMNS = 4
SLICE_SIZE = 4
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

#[END Global variables]


class Dropzone(ndb.Model):
    name = ndb.StringProperty()
    defaultloadtime = ndb.IntegerProperty()
    defaultloadnumber = ndb.IntegerProperty()
    defaultslotnumber = ndb.IntegerProperty()
    status = ndb.IntegerProperty()


class Load(ndb.Model):
    number = ndb.IntegerProperty()
    slots = ndb.IntegerProperty()      # total slots on the load
    precededby = ndb.IntegerProperty()
    time = ndb.TimeProperty()
    date = ndb.DateProperty(auto_now_add=True)
    status = ndb.IntegerProperty()
    dropzone = ndb.IntegerProperty()

    @classmethod
    def get_loads (cls, dropzone_key) :
        return cls.query(Load.date == datetime.date.today(),Load.dropzone == dropzone_key).order(Load.number)

    @classmethod
    def add_load (cls, loads, dropzone_key) :
        dropzone = Dropzone.get_by_id(dropzone_key)
        last = len(loads) - 1
        time_increment = datetime.timedelta(minutes=dropzone.defaultloadtime)
        if last >= 0:
            load = Load(number=loads[last].number + 1,
                        slots=dropzone.defaultslotnumber,
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
    def get_user (cls, name) :
        return cls.query(User.name == name)

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

    @classmethod
    def get_by_email(cls, email):
        return cls.query(Jumper.email == email)

def LoadStructure (loads) :
    manifests = Manifest.query().fetch()
    slot_mega = {}
    for load in loads :
        slots = []
        for manifest in manifests :
            if manifest.load == load.key.id() :
                slots.append(Jumper.get_by_id(manifest.jumper))
        slot_mega.update({load.key.id() : slots})
    return slot_mega


def FreeSlots(loads, slot_mega, dropzone_key):
    frees = {}
    slotnumber = Dropzone.get_by_id(dropzone_key).defaultslotnumber
    if slotnumber:
        for load in loads:
            free = slotnumber - len(slot_mega[load.key.id()])
            frees.update({load.key.id(): free})
    return frees


def JumperStructure (dropzone_key) :
    registrations = Registration.get_by_dropzone(dropzone_key).fetch()
    jumpers = []
    for registration in registrations :
        jumper_key = registration.jumper
        jumpers.append((Jumper.get_by_id(jumper_key), registration))
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
    loads = Load.get_loads(dropzone_key).fetch()
    manifests = Manifest.get_by_load(load.key.id())
    for next_load in loads:
        if next_load.precededby == load.key.id():
            next_load.precededby = load.precededby
            next_load.put()
    load.key.delete()
    # Have to refresh loads to avoid re-inserting the deleted load
    loads = Load.get_loads(dropzone_key).fetch()
    # Retime all loads
    if len(loads) != 0:
        loads = RetimeChain(loads[0], loads, Dropzone.get_by_id(dropzone_key))
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


# retimes a list of loads using the precededby parameter - starting with load
def RetimeChain(load, loads, dropzone):
    flag = True
    while flag:
        flag = False
        for next_load in loads:
            if next_load.precededby == load.key.id():
                if next_load.status in [WAITING, HOLD]:
                    next_load.time = NextLoadTimeDz(load, dropzone)
                load = next_load
                load.put()
                flag = True
                break
    return loads
