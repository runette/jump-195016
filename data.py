import datetime

from google.appengine.api import users
from google.appengine.ext import ndb


#[START Global variables]

DEFAULT_DROPZONE_NAME = "No Dropzone"  # deprecated
DEFAULT_DROPZONE_ID = 5659313586569216
DEFAULT_DROPZONE_STATUS = "No Status"  # deprecated
DROPZONE_OPEN = "Open"
DROPZONE_CLOSED = "Closed"
LOAD_STATUS = ["Waiting","In the air", "On hold", "Landed"] # - waiting, flying, hold, landed
DEFAULT_LOAD_ID = 0
REGISTRATION_STATUS = ["Current", "Not Current"]
USER_ROLES = ["admin", "manifest", "sales", "view"]  # - admin, manifest, sales, view
ADMIN = 0
MANIFEST = 1
SALES = 2
VIEW = 3

#[END Global variables]


class Dropzone(ndb.Model):
    name = ndb.StringProperty()
    defaultloadtime = ndb.IntegerProperty()
    defaultloadnumber = ndb.IntegerProperty()
    defaultslotnumber = ndb.IntegerProperty()
    status = ndb.StringProperty()


class Load(ndb.Model):
    number = ndb.IntegerProperty()
    slots = ndb.IntegerProperty()      # total slots on the load
    precededby = ndb.IntegerProperty()
    time = ndb.TimeProperty()
    date = ndb.DateProperty(auto_now_add=True)
    status = ndb.StringProperty()
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
                        status=LOAD_STATUS[0],
                        time=(datetime.datetime.combine(datetime.date(1, 1, 1),
                                                        loads[last].time) + time_increment).time(),
                        dropzone=dropzone_key
                        )
        else:
            load = Load(
                number=1,
                slots=dropzone.defaultloadnumber,
                precededby=-1,
                status=LOAD_STATUS[0],
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
    current = ndb.StringProperty()

    @classmethod
    def get_by_dropzone (cls, dropzone) :
        return cls.query(Registration.dropzone == dropzone, Registration.current == REGISTRATION_STATUS[0]).order(Registration.jumper)


class Sale(ndb.Model) :
    jumper = ndb.IntegerProperty()
    dropzone = ndb.IntegerProperty()
    name = ndb.StringProperty()
    jumps_remaining = ndb.IntegerProperty()


class Jumper(ndb.Model):
    name = ndb.StringProperty()


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
        jumpers.append(Jumper.get_by_id(jumper_key))
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


def DeleteLoad(load) :
    manifests = Manifest.get_by_load(load.key.id())
    load.key.delete()
    for manifest in manifests :
         manifest.key.delete()