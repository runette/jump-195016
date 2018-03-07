# !/usr/bin/env python
# Copyright 2018 Paul Harwood
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# [START imports]


import webapp2

import datetime
from data import *


# [END Imports]

# MainPage handles the index page
class MainPage(webapp2.RequestHandler):
    def get(self):
        user_data = UserStatus(self.request.uri)
        user = user_data['user']

        if user:
            # Get the dropzone details based on the user
            dropzone_key = User.get_user(user.email()).fetch()[0].dropzone
            dropzone = Dropzone.get_by_id(dropzone_key)
        else:
            dropzone = Dropzone.get_by_id(DEFAULT_DROPZONE_ID)
        dropzone_status = dropzone.status
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'active': 0,
            'dropzone_status': DROPZONE_STATUS
        }
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

#Handles Start of Day actions and returns to the index page
class StartDay(webapp2.RequestHandler):
    def get(self):
        user_data = UserStatus(self.request.uri)
        user = user_data['user']
        if user:
            #change status to open and add a default number of loads
            dropzone_key = int(self.request.get('dropzone', DEFAULT_DROPZONE_ID))
            dropzone = Dropzone.get_by_id(dropzone_key)
            dropzone.status = OPEN
            Dropzone.put(dropzone)
            for i in range(dropzone.defaultloadnumber):
                loads = Load.get_loads(dropzone_key).fetch()
                Load.add_load(loads, dropzone_key).put()

        else:
            dropzone = Dropzone.get_by_id(DEFAULT_DROPZONE_ID)

        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'active': 0,
            'dropzone_status': DROPZONE_STATUS

        }
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

#Handles end of day actions and returns to the main page
class EndDay(webapp2.RequestHandler):
    def get(self):
        user_data = UserStatus(self.request.uri)
        user = user_data['user']
        # change status to closed and delete all loads that did not take off
        if user:
            dropzone_key = int(self.request.get('dropzone', DEFAULT_DROPZONE_ID))
            dropzone = Dropzone.get_by_id(dropzone_key)
            dropzone.status = CLOSED
            loads = Load.get_loads(dropzone_key).fetch()
        else:
            dropzone = Dropzone.get_by_id(DEFAULT_DROPZONE_ID)
            loads = []
        for load in loads:
            if load.status in [WAITING, HOLD]: load.key.delete()
            DeleteLoad(load, dropzone_key)
        Dropzone.put(dropzone)
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'active': 0,
            'dropzone_status': DROPZONE_STATUS
        }
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class ManageSales(webapp2.RequestHandler):
    def get(self):
        user_data = UserStatus(self.request.uri)

        dropzone_key = int(self.request.get('dropzone', DEFAULT_DROPZONE_ID))
        dropzone = Dropzone.get_by_id(dropzone_key)

        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'active': 2,
            'dropzone_status': DROPZONE_STATUS
        }
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class ManageLoads(webapp2.RequestHandler):
    def get(self):
        user_data = UserStatus(self.request.uri)
        # GET PARAMETERS
        load_key = int(self.request.get('load', DEFAULT_LOAD_ID))
        action = self.request.get('action')
        message = {}
        user = User.get_user(user_data['user'].email()).fetch()[0]
        dropzone_key = int(self.request.get('dropzone'))
        # Set the Dropone details
        dropzone = Dropzone.get_by_id(dropzone_key)
        dropzone_status = dropzone.status
        # Set the Load Details
        loads = Load.get_loads(dropzone_key).fetch()
        if user.role in [ADMIN, MANIFEST]:
            if action == "takeoff":
                load = Load.get_by_id(load_key)
                load.status = FLYING
                load.put()
            if action == "add":
                if dropzone_status == OPEN:
                    Load.add_load(loads, dropzone_key).put()
                else:
                    message.update({'title': "Cannot Add"})
                    message.update(
                        {'body': dropzone.name + " is currently closed so new loads cannot be added "})
            if action == "landed":
                load = Load.get_by_id(load_key)
                load.status = LANDED
                load.put()
            if action == "hold":
                load = Load.get_by_id(load_key)
                load.status = HOLD
                load.put()
            if action == "delete":
                load = Load.get_by_id(load_key)
                if load.status in [WAITING, HOLD]:
                    DeleteLoad(load, dropzone_key)
                else:
                    message.update({'title': "Cannot Delete"})
                    message.update(
                        {'body': "Cannot delete loads that have taken off - use end of day function "})

        else:
            message.update({'title': "Cannot Manifest"})
            message.update(
                {'body': "You do not have Manifest rights "})

        # refresh loads
        loads = Load.get_loads(dropzone_key).fetch()
        slot_mega = LoadStructure(loads)
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'loads': loads,
            'slot_mega': slot_mega,
            'message': message,
            'slotsize': FreeSlots(loads, slot_mega, dropzone_key),
            'active': 1,
            'dropzone_status': DROPZONE_STATUS,
            'load_status': LOAD_STATUS,
        }
        template = JINJA_ENVIRONMENT.get_template('loads.html')
        self.response.write(template.render(template_values))



class ManageManifest(webapp2.RequestHandler):
    def get(self):
        user_data = UserStatus(self.request.uri)
        # GET PARAMETERS
        dropzone_key = int(self.request.get('dropzone', DEFAULT_DROPZONE_ID))
        load_key = int(self.request.get('load', DEFAULT_LOAD_ID))
        action = self.request.get('action')
        jumper_key = self.request.get('jumper')
        message = {}
        user = User.get_user(user_data['user'].email()).fetch()[0]
        if jumper_key:
            jumper_key = int(jumper_key)
        # Set the Dropone details
        dropzone = Dropzone.get_by_id(dropzone_key)

        # Set the Load Details

        load = Load.get_by_id(load_key)
        loads = [load]
        slot_mega = LoadStructure(loads)
        slot_size = FreeSlots(loads, slot_mega, dropzone_key)
        if user.role in [ADMIN, MANIFEST]:
            if action == "add":
                if load.status in [WAITING, HOLD]:
                    if slot_size[load.key.id()] > 0:
                        manifest = Manifest(
                            load=load_key,
                            jumper=jumper_key
                        )
                        manifest.put()

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
                    Manifest.delete_manifest(load_key, jumper_key)
                else:
                    message.update({'title': "Cannot Delete"})
                    message.update(
                        {'body': "Cannot delete loads that have taken off - use end of day function "})

        else:
            message.update({'title': "Cannot Manifest"})
            message.update(
                {'body': "You do not have Manifest rights "})

        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'load': load,
            'slot_mega': LoadStructure(loads),
            'slotsize': FreeSlots(loads, slot_mega, dropzone_key),
            'jumpers': JumperStructure(dropzone_key),
            'message': message,
            'active': 1,
            'dropzone_status': DROPZONE_STATUS,
            'load_status': LOAD_STATUS
        }
        template = JINJA_ENVIRONMENT.get_template('manifest.html')
        self.response.write(template.render(template_values))


class ManageJumpers(webapp2.RequestHandler):
    def get(self):
        user_data = UserStatus(self.request.uri)
        # GET PARAMETERS
        jumper_key = int(self.request.get('jumper', "0"))
        action = self.request.get('action')
        message = {}
        user = User.get_user(user_data['user'].email()).fetch()[0]
        dropzone_key = int(self.request.get('dropzone'))
        dropzone = Dropzone.get_by_id(dropzone_key)

        if user.role in [ADMIN, SALES]:
            if action == "add":
                jumper_email = self.request.get('email') + "@gmail.com"
                jumper = Jumper.get_by_email(jumper_email).fetch()
                if jumper:
                    registration = Registration(
                        jumper=jumper[0].key.id(),
                        dropzone=dropzone_key,
                        waiver=datetime.date.today(),
                        reserve=datetime.date.today(),
                        current=NOT_CURRENT
                    )
                    registration.put()
                else:
                    message.update({'title': "Invalid Jumper"})
                    message.update(
                        {'body': "No Jumper registered with this email"})
            if action == "update":
                registration = Registration.get_by_jumper(dropzone_key, jumper_key).fetch()[0]
                registration.waiver = datetime.datetime.strptime(self.request.get('waiver'), "%d/%m/%y")
                registration.reserve = datetime.datetime.strptime(self.request.get('reserve'), "%d/%m/%y")
                registration.current = int(self.request.get('current', "1"))
                registration.put()
            if action == "delete":
                registration = Registration.get_by_jumper(dropzone_key, jumper_key).fetch()[0]
                if registration:
                    registration.key.delete()
        else:
            message.update({'title': "Cannot Registration"})
            message.update(
                {'body': "You do not have Registration rights "})

        # refresh registrations
        registrations = Registration.get_by_dropzone(dropzone_key).fetch()
        jumpers = JumperStructure(dropzone_key)
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'registration': registrations,
            'jumpers': jumpers,
            'message': message,
            'active': 3,
            'dropzone_status': DROPZONE_STATUS,
            'registration_status': REGISTRATION_STATUS,
            'registration_colours': REGISTRATION_COLOURS
        }
        template = JINJA_ENVIRONMENT.get_template('jumpers.html')
        self.response.write(template.render(template_values))


class ManageDz(webapp2.RequestHandler):
    def get(self):
        user_data = UserStatus(self.request.uri)
        user = User.get_user(user_data['user'].email()).fetch()[0]
        message = {}
        if user.role == ADMIN:
            # Get the dropzone details based on the user
            dropzone_key = int(self.request.get('dropzone'))
            dropzone = Dropzone.get_by_id(dropzone_key)
        else:
            dropzone_key = DEFAULT_DROPZONE_ID
            dropzone = Dropzone.get_by_id(dropzone_key)
            message.update({'title': "Not Administrator"})
            message.update({'body': "You do not have administrator rights"})
        action = self.request.get('action')
        if action == "user":
            response = "configureuser.html"
        elif action == "sales":
            response = "configuresales.html"
        elif action == "kiosk":
            response = "configurekiosk.html"
        else:
            response = "configuredz.html"


        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'users': User.get_by_dropzone(dropzone_key).fetch(),
            'message': message,
            'user_roles': USER_ROLES,
            'role_colours': ROLE_COLOURS,
            'active': 4,
            'dropzone_status': DROPZONE_STATUS,
            'packages': SalesPackage.get_by_dropzone(dropzone_key).fetch()

        }
        template = JINJA_ENVIRONMENT.get_template(response)
        self.response.write(template.render(template_values))


class UpdateDz(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = User.get_user(user_data['user'].email()).fetch()[0]
        dropzone_key = int(self.request.get('dropzone'))
        if user.role == ADMIN:
            # GET PARAMETERS
            dropzone = Dropzone.get_by_id(dropzone_key)
            dropzone.name = self.request.get('dropzone_name')
            dropzone.defaultslotnumber = int(self.request.get('default_slot_number'))
            dropzone.defaultloadnumber = int(self.request.get('default_load_number'))
            dropzone.defaultloadtime = int(self.request.get('default_load_time'))
            dropzone.tag = self.request.get('dropzone_tag')
            dropzone.put()
        self.redirect('/configdz?dropzone=' + str(dropzone_key) + '&action=dz')


class UpdateUser(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = User.get_user(user_data['user'].email()).fetch()[0]
        dropzone_key = int(self.request.get('dropzone'))
        action = self.request.get('action')
        user_key = int(self.request.get('user', '-1'))
        if user.role == ADMIN:
            if action == "update":
                # GET PARAMETERS
                user_update = User.get_by_id(user_key)
                if user_update:
                    user_update.role = int(self.request.get('user_role'))
                    user_update.dropzone = dropzone_key
                    user_update.put()
            if action == "add":
                user_update = User(
                    name=self.request.get('user_email') + "@gmail.com",
                    dropzone=dropzone_key,
                    role=VIEW
                )
                user_update.put()
            if action == "delete":
                user_update = User.get_by_id(user_key)
                if user_update:
                    user_update.key.delete()
        self.redirect('/configdz?dropzone=' + str(dropzone_key) + '&action=user')


class UpdateSales(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = User.get_user(user_data['user'].email()).fetch()[0]
        dropzone_key = int(self.request.get('dropzone'))
        action = self.request.get('action')
        package_key = int(self.request.get('package', '-1'))
        if user.role == ADMIN:
            if action == "update":
                # GET PARAMETERS
                package = SalesPackage.get_by_id(package_key)
                if package:
                    package.size = int(self.request.get('sales_size'))
                    package.name = self.request.get('sales_name')
                    package.put()
            if action == "add":
                package = SalesPackage(
                    name=self.request.get('sales_name'),
                    dropzone=dropzone_key,
                    size=0
                )
                package.put()
            if action == "delete":
                package = SalesPackage.get_by_id(package_key)
                if package:
                    package.key.delete()
        self.redirect('/configdz?dropzone=' + str(dropzone_key) + '&action=sales')



class RetimeLoads(webapp2.RequestHandler):
    def get(self):
        user_data = UserStatus(self.request.uri)
        user = User.get_user(user_data['user'].email()).fetch()[0]
        message = {}
        load_key = int(self.request.get('load', DEFAULT_LOAD_ID))
        action = self.request.get('action')
        dropzone_key = int(self.request.get('dropzone'))
        # Set the Dropone details
        dropzone = Dropzone.get_by_id(dropzone_key)
        if user.role in [ADMIN, MANIFEST]:
            # Set the Dropone details
            dropzone = Dropzone.get_by_id(dropzone_key)
            loads = Load.get_loads(dropzone_key).fetch()
            load = Load.get_by_id(load_key)
            if action == "5":
                load.time = NextLoadTime(load, datetime.timedelta(minutes=5))
                load.put()
            if action == "10":
                load.time = NextLoadTime(load, datetime.timedelta(minutes=10))
                load.put()
            if action == "select":
                load.time = NextLoadTime(load, datetime.timedelta(minutes=0))
            loads = RetimeChain(load, loads, dropzone)

        else:
            message.update({'title': "Cannot Manifest"})
            message.update(
                {'body': "You do not have Manifest rights "})

        # refresh loads
        loads = Load.get_loads(dropzone_key).fetch()
        slot_mega = LoadStructure(loads)
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'loads': loads,
            'slot_mega': slot_mega,
            'message': message,
            'slotsize': FreeSlots(loads, slot_mega, dropzone_key),
            'active': 1,
            'dropzone_status': DROPZONE_STATUS,
            'load_status': LOAD_STATUS,
        }
        template = JINJA_ENVIRONMENT.get_template('loads.html')
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/loads', ManageLoads),
    ('/startday', StartDay),
    ('/endday', EndDay),
    ('/sales', ManageSales),
    ('/manifest', ManageManifest),
    ('/loadaction', ManageLoads),
    ('/manifestaction', ManageManifest),
    ('/jumpers', ManageJumpers),
    ('/configdz', ManageDz),
    ('/updatedz', UpdateDz),
    ('/updateuser', UpdateUser),
    ('/retime', RetimeLoads),
    ('/updatesales', UpdateSales)

], debug=True)
