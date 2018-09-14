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
            dropzone_key = User.get_user(user.email()).dropzone
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
        message = {}
        dropzone_key = int(self.request.get('dropzone', DEFAULT_DROPZONE_ID))
        dropzone = Dropzone.get_by_id(dropzone_key)
        if dropzone.status == CLOSED:
            #change status to open and add a default number of loads
            dropzone.status = OPEN
            Dropzone.put(dropzone)
            ls = LoadStructure(dropzone_key)
            if len(ls.loads) is 0 :
                for i in range(dropzone.default_load_number):
                    ls.add_load()
        elif dropzone.status == OPEN:
            message.update({'title': "Already Open"})
            message.update(({'body': "The dropzone is already open"}))
        else:
            message.update({'title': "Problem"})
            message.update(({'body': "Something went wrong"}))

        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'active': 0,
            'dropzone_status': DROPZONE_STATUS,
            'message': message,

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
            if load.status in [WAITING, HOLD]:
                ls=LoadStructure(dropzone_key)
                ls.delete_load(load)
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
        user = User.get_user(user_data['user'].email())
        dropzone_key = int(self.request.get('dropzone'))
        # Set the Dropone details
        dropzone = Dropzone.get_by_id(dropzone_key)
        dropzone_status = dropzone.status
        load_struct = LoadStructure(dropzone_key)
        # Set the Load Details
        if user.role in [ADMIN, MANIFEST]:
            if action == "takeoff":
                load = Load.get_by_id(load_key)
                load.status = FLYING
                load.put()
            if action == "add":
                if dropzone_status == OPEN:
                    load_struct.add_load()
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
            if action == "delete":
                load = Load.get_by_id(load_key)
                if load.status in [WAITING, HOLD]:
                    load_struct.delete_load(load)
                    load_struct.retime_chain()
                else:
                    message.update({'title': "Cannot Delete"})
                    message.update(
                        {'body': "Cannot delete loads that have taken off - use end of day function "})

        else:
            message.update({'title': "Cannot Manifest"})
            message.update(
                {'body': "You do not have Manifest rights "})

        # refresh loads
        loads = load_struct.loads
        slot_mega = load_struct.slot_mega
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'loads': loads,
            'slot_mega': slot_mega,
            'message': message,
            'slotsize': load_struct.freeslots(),
            'active': 1,
            'dropzone_status': DROPZONE_STATUS,
            'load_status': LOAD_STATUS,
            'load_colours': LOAD_COLOURS
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
        jumper_key = int(self.request.get('jumper', "0"))
        message = {}
        user = User.get_user(user_data['user'].email())
        # Set the Dropone details
        dropzone = Dropzone.get_by_id(dropzone_key)
        registrations = Registration.get_by_jumper(dropzone_key, jumper_key).fetch()
        if registrations:
            registration = registrations[0]

        # Set the Load Details
        load = Load.get_by_id(load_key)
        load_struct = LoadStructure(dropzone_key)
        slot_size = load_struct.freeslots()
        if user.role in [ADMIN, MANIFEST]:
            if action == "add":
                if load.status in [WAITING, HOLD]:
                    if slot_size[load.key.id()] > 0:
                        if registration.current == CURRENT:
                            load_struct.add_manifest(load_key,jumper_key)
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
                    Manifest.delete_manifest(load_key, jumper_key)
                    load_struct.refresh()
                else:
                    message.update({'title': "Cannot Delete"})
                    message.update(
                        {'body': "Cannot delete loads that have taken off - use end of day function "})

        else:
            message.update({'title': "Cannot Manifest"})
            message.update(
                {'body': "You do not have Manifest rights "})

        #Refresh the Manifests


        slot_mega = load_struct.slot_mega
        slot_size = load_struct.freeslots()
        js=JumperStructure(dropzone_key)
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'load': load,
            'slot_mega': slot_mega,
            'slotsize': slot_size,
            'jumpers': js.jumpers,
            'message': message,
            'active': 1,
            'dropzone_status': DROPZONE_STATUS,
            'load_status': LOAD_STATUS,
            'load_colours': LOAD_COLOURS
        }
        template = JINJA_ENVIRONMENT.get_template('manifest.html')
        self.response.write(template.render(template_values))


class ManageJumpers(webapp2.RequestHandler):
    def get(self):
        user_data = UserStatus(self.request.uri)
        # GET PARAMETERS
        jumper_key = int(self.request.get('jumper', "0"))
        action = self.request.get('action')
        delete = self.request.get('delete')
        message = {}
        user = User.get_user(user_data['user'].email())
        dropzone_key = int(self.request.get('dropzone'))
        dropzone = Dropzone.get_by_id(dropzone_key)

        if user.role in [ADMIN, SALES]:
            if action == "add":
                jumper_email = self.request.get('email') + "@gmail.com"
                jumper = Jumper.get_by_email(jumper_email).fetch()
                if jumper:
                    jumper_key = jumper[0].key.id()
                    registration = Registration.get_by_jumper(dropzone_key, jumper_key).fetch()
                    if registration:
                        message.update({'title': "Double Registration"})
                        message.update({'body': " Cannot register a jumper twice"})
                    else:
                        registration = Registration(
                            jumper=jumper_key,
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

            if delete == "yes":
                registration = Registration.get_by_jumper(dropzone_key, jumper_key).fetch()[0]
                if registration.current == NOT_CURRENT:
                    registration.delete()
                else:
                    message.update({'title': "Current Jumper"})
                    message.update({'body': "Cannot delete a current jumper. Make them uncurrent first"})

            elif action == "update":
                registration = Registration.get_by_jumper(dropzone_key, jumper_key).fetch()[0]
                registration.waiver = datetime.datetime.strptime(self.request.get('waiver'), "%d/%m/%y")
                registration.reserve = datetime.datetime.strptime(self.request.get('reserve'), "%d/%m/%y")
                registration.current = int(self.request.get('current', "1"))
                registration.put()
        else:
            message.update({'title': "Cannot Registration"})
            message.update(
                {'body': "You do not have Registration rights "})

        # refresh registrations
        registrations = Registration.get_by_dropzone(dropzone_key).fetch()
        js = JumperStructure(dropzone_key)
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'registration': registrations,
            'jumpers': js.jumpers,
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
        user = User.get_user(user_data['user'].email())
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
            'packages': SalesPackage.get_by_dropzone(dropzone_key).fetch(),
            'request' : self.request.application_url,

        }
        template = JINJA_ENVIRONMENT.get_template(response)
        self.response.write(template.render(template_values))


class UpdateDz(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = User.get_user(user_data['user'].email())
        dropzone_key = int(self.request.get('dropzone'))
        if user.role == ADMIN:
            # GET PARAMETERS
            dropzone = Dropzone.get_by_id(dropzone_key)
            dropzone.name = self.request.get('dropzone_name')
            dropzone.default_slot_number = int(self.request.get('default_slot_number'))
            dropzone.default_load_number = int(self.request.get('default_load_number'))
            dropzone.default_load_time = int(self.request.get('default_load_time'))
            dropzone.tag = self.request.get('dropzone_tag')
            dropzone.put()
        self.redirect('/configdz?dropzone=' + str(dropzone_key) + '&action=dz')


class UpdateUser(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = User.get_user(user_data['user'].email())
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
                name = self.request.get('user_email') + "@gmail.com"
                user_update = User.get_user(name)
                user_update = User(
                        name=name,
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
        user = User.get_user(user_data['user'].email())
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
        user = User.get_user(user_data['user'].email())
        message = {}
        load_key = int(self.request.get('load', DEFAULT_LOAD_ID))
        action = self.request.get('action')
        dropzone_key = int(self.request.get('dropzone'))
        # Set the Dropone details
        dropzone = Dropzone.get_by_id(dropzone_key)
        if user.role in [ADMIN, MANIFEST]:
            # Set the Dropone details
            load = Load.get_by_id(load_key)
            if action == "5":
                load.time = NextLoadTime(load, datetime.timedelta(minutes=5))
                load.put()
            if action == "10":
                load.time = NextLoadTime(load, datetime.timedelta(minutes=10))
                load.put()
            if action == "select":
                load.time = NextLoadTime(load, datetime.timedelta(minutes=0))
            load_struct = LoadStructure(dropzone_key)
            load_struct.retime_chain()

        else:
            message.update({'title': "Cannot Manifest"})
            message.update(
                {'body': "You do not have Manifest rights "})

        # refresh loads
        load_struct = LoadStructure(dropzone_key)
        loads = load_struct.loads
        slot_mega = load_struct.slot_mega
        slot_size = load_struct.freeslots()
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'loads': loads,
            'slot_mega': slot_mega,
            'message': message,
            'slotsize': slot_size,
            'active': 1,
            'dropzone_status': DROPZONE_STATUS,
            'load_status': LOAD_STATUS,
            'load_colours': LOAD_COLOURS
        }
        template = JINJA_ENVIRONMENT.get_template('loads.html')
        self.response.write(template.render(template_values))

class NewDz(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = User.get_user(user_data['user'].email())
        dropzone = Dropzone(name="New Dropzone",
                default_load_time=0,
                default_load_number=0,
                default_slot_number=0,
                status=CLOSED,
                tag="",
                kiosk_cols=1,
                kiosk_rows=1,)
        dropzone.put()
        user.dropzone = dropzone.key.id()
        user.role = ADMIN
        user.put()
        self.redirect('/configdz?dropzone=' + str(dropzone.key.id()) + '&action=dz')


