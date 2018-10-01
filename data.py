import datetime

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import memcache

import os
import jinja2

# START Global variables


DROPZONE_STATUS = ["Open", "Closed"]
OPEN = 0
CLOSED = 1
DEFAULT_DROPZONE_NAME = "No Dropzone"
DEFAULT_DROPZONE_ID = 0
DEFAULT_DROPZONE_STATUS = CLOSED
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

DEFAULT_DROPZONE = {
    'name': DEFAULT_DROPZONE_NAME,
    'status': -1,
    'key': {'id':DEFAULT_DROPZONE_ID}
}

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



class Manifest(ndb.Model):
    load = ndb.IntegerProperty()  # The key for the load that this manifest applies to
    jumper = ndb.IntegerProperty() # The key for jumper this applies to
    sale = ndb.IntegerProperty()

    @classmethod
    def get_by_load(cls, load_key):
        return cls.query(Manifest.load == load_key)

    @classmethod
    def get_by_sale(cls, sale_key):
        return cls.query(Manifest.sale == sale_key).fetch()

    @classmethod
    def get_sale_usage(cls, sale_key):
        used = cls.get_by_sale(sale_key)
        return len(used)



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


class SalesPackage(ndb.Model):
    name = ndb.StringProperty()
    dropzone = ndb.IntegerProperty()
    description = ndb.StringProperty()
    size = ndb.IntegerProperty()

    @classmethod
    def get_by_dropzone(cls, dropzone_key):
        return cls.query(SalesPackage.dropzone == dropzone_key).order(SalesPackage.name).fetch()


class Sale(ndb.Model) :
    jumper = ndb.IntegerProperty()
    dropzone = ndb.IntegerProperty()
    package = ndb.IntegerProperty()

    @classmethod
    def get_sales(cls, dropzone_key, jumper_key):
        return cls.query(Sale.jumper == jumper_key, Sale.dropzone == dropzone_key).order(Sale.package)


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
        self.save()
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
        sm=SalesMega(self.dropzone_key,jumper_key)
        for id, sale in sm.sales.iteritems():
            if sale['free'] >0:
                manifest = Manifest(
                    load=load_key,
                    jumper=jumper_key,
                    sale=id
                )
                manifest.put()
                slots = self.slot_mega[load_key]
                slots.append(Jumper.get_by_id(manifest.jumper))
                self.save()
                sm.use(id)
                sm.save()
                break
        return

    def delete_manifest(self, load_key, jumper_key):
        manifest = Manifest.query(Manifest.load == load_key, Manifest.jumper == jumper_key).get()
        slots = self.slot_mega[load_key]
        jumper = Jumper.get_by_id(jumper_key)
        sm=SalesMega(self.dropzone_key, jumper_key)
        sale_key = manifest.sale
        manifest.key.delete()
        slots.remove(jumper)
        sm.un_use(sale_key)
        sm.save()
        self.save()
        return

    def retime_load(self, load_key, minutes):
        for load in self.loads:
            if load.key.id() == load_key:
                load.time = NextLoadTime(load, datetime.timedelta(minutes=minutes))
                load.put()
        self.retime_chain()
        return

    def set_status(self, load_key, status):
        for load in self.loads:
            if load.key.id() == load_key:
                load.status = status
                load.put()
        self.save()
        return

    def manifest_action(self, action, load, registration):
        message = {}
        slot_size = self.freeslots()
        if action == "add":
            if load.status in [WAITING, HOLD]:
                if slot_size[load.key.id()] > 0:
                    if registration.current == CURRENT:
                        self.add_manifest(load.key.id(), registration.jumper)
                    else:
                        message.update({'title': "Not Current"})
                        message.update({'body': "Cannot Manifest a Jumper who is not Current"})
                else:
                    message.update({'title': "No Slots"})
                    message.update({'body': "You cannot manifest on this load - there are no slots left"})
            else:
                message.update({'title': "Cannot Add"})
                message.update(
                    {'body': "This Load is not Open for Manifest. The Load status is \" " + LOAD_STATUS[
                        load.status] + "\""})
        if action == "delete":
            if load.status in [WAITING, HOLD]:
                self.delete_manifest(load.key.id(), registration.jumper)
            else:
                message.update({'title': "Cannot Delete"})
                message.update(
                    {'body': "Cannot delete loads that have taken off - use end of day function "})

class JumperStructure :
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

    def delete(self, jumper_key):
        registration = Registration.get_by_jumper(self.dropzone_key, jumper_key).get()
        jumper = Jumper.get_by_id(jumper_key)
        try:
            self.jumpers.remove((jumper, registration))
        except ValueError:
            pass
        registration.key.delete()
        self.save()
        return

    def add(self, jumper_key):
        registration = Registration(
            jumper=jumper_key,
            dropzone=self.dropzone_key,
            waiver=datetime.date.today(),
            reserve=datetime.date.today(),
            current=NOT_CURRENT
        )
        registration.put()
        self.jumpers.append((Jumper.get_by_id(jumper_key), registration))
        self.save()
        return

    def update(self, jumper_key, waiver, reserve, current):
        registration = Registration.get_by_jumper(self.dropzone_key, jumper_key).get()
        jumper= Jumper.get_by_id(jumper_key)
        try :
            self.jumpers.remove((jumper, registration))
        except ValueError:
            pass
        registration.waiver = waiver
        registration.reserve = reserve
        registration.current = current
        registration.put()
        self.jumpers.append((jumper, registration))
        self.save()
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


class RegMega:
    reg_mega = []

    def __init__(self,user):
        self.user = user
        self.key = user.user_id()
        client = memcache.Client()
        content = client.get(self.key)
        if content:
            self.reg_mega = content
            self.jumper = Jumper.get_by_gid(self.user.user_id()).get().key.id()
        else:
            self.refresh()
        return


    def refresh(self):
        self.reg_mega = []
        jumper = Jumper.get_by_gid(self.user.user_id()).get()
        if jumper:
            self.jumper = jumper.key.id()
            registrations = Registration.get_all_by_jumper(self.jumper)
            for registration in registrations:
                self.reg_mega.append((registration, Dropzone.get_by_id(registration.dropzone)))
        else:
            jumper = Jumper(
                name=self.user.nickname(),
                email=self.user.email(),
                google_id=self.user.user_id(),
            )
            jumper.put()
            self.jumper = jumper.key.id()
        self.save()
        return

    def save(self):
        client = memcache.Client()
        while True:  # Retry loop
            content = client.gets(self.key)
            if content is None:
                memcache.set(self.key, self.reg_mega,time=1000)
                break
            if client.cas(self.key, self.reg_mega, time=1000):
                break
        return

class SalesMega:
    sales={}

    def __init__(self, dropzone_key, jumper_key):
        self.dropzone_key = dropzone_key
        self.jumper_key = jumper_key
        self.key = str(dropzone_key) + str(jumper_key)
        client = memcache.Client()
        content = client.get(self.key)
        if content:
            self.sales = content
        else:
            self.refresh()
        return

    def refresh(self):
        self.sales = {}
        all_sales = Sale.get_sales(self.dropzone_key,self.jumper_key)
        for sale in all_sales:
            usage = Manifest.get_sale_usage(sale.key.id())
            sp = SalesPackage.get_by_id(sale.package)
            free = sp.size - usage
            sale_detail = {
                'details' : sp,
                'free' : free,
            }
            self.sales.update({sale.key.id():sale_detail})
        self.save()
        return

    def save(self):
        client = memcache.Client()
        while True:  # Retry loop
            content = client.gets(self.key)
            if content is None:
                memcache.set(self.key, self.sales,time=1000)
                break
            if client.cas(self.key, self.sales, time=1000):
                break
        return

    def use(self, sale_key):
        self.sales[sale_key]['free'] = self.sales[sale_key]['free'] -1
        self.save()
        return

    def un_use(self, sale_key):
        self.sales[sale_key]['free'] = self.sales[sale_key]['free'] +1
        self.save()
        return

    def sell(self, package_key):
        package = SalesPackage.get_by_id(package_key)
        sale = Sale(
            dropzone=self.dropzone_key,
            jumper=self.jumper_key,
            package=package_key
        )
        sale.put()
        sale_detail = {
            'details': package,
            'free': package.size,
        }
        self.sales.update({sale.key.id(): sale_detail})
        self.save()
        return

    def change_sale(self, from_sale, to_sale, load_key, jumper_key):
        manifest = Manifest.query(Manifest.load == load_key, Manifest.jumper == jumper_key).get()
        try:
            self.un_use(from_sale)
            self.use(to_sale)
            manifest.sale = to_sale
        except Exception :
            self.refresh()
            return
        manifest.put()
        return
