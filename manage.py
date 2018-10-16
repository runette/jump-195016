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

import logging
import json

import datetime
from data import *


# [END Imports]

# MainPage handles the index page
class MainPage(webapp2.RequestHandler):
    def get(self):
        if self.request.referer:
            if "client" in self.request.referer:
                self.redirect('/client')
                return
            if "kiosk" in self.request.referer and "configdz" not in self.request.referer:
                self.redirect(self.request.referer)
                return
        user_data = UserStatus(self.request.uri)
        user = user_data['user']
        if user:
            # Get the dropzone details based on the user
            dropzone_key = User.get_user(user.email()).dropzone
            dropzone = Dropzone.get_by_id(dropzone_key)
        else:
            dropzone = DEFAULT_DROPZONE
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'active': 0,
            'dropzone_status': DROPZONE_STATUS
        }
        template = JINJA_ENVIRONMENT.get_template('manage.html')
        self.response.write(template.render(template_values))
        return

class MainIndex(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = user_data['user']
        if user:
            # Get the dropzone details based on the user
            dropzone_key = User.get_user(user.email()).dropzone
            dropzone = Dropzone.get_by_id(dropzone_key)
        else:
            dropzone = DEFAULT_DROPZONE
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'active': 0,
            'dropzone_status': DROPZONE_STATUS,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
        return

#Handles Start of Day actions and returns to the index page
class StartDay(webapp2.RequestHandler):
    def post(self):
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
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'active': 0,
            'dropzone_status': DROPZONE_STATUS
        }
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
        return

#Handles end of day actions and returns to the main page
class EndDay(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = user_data['user']
        # change status to closed and delete all loads that did not take off
        if user:
            dropzone_key = int(self.request.get('dropzone', DEFAULT_DROPZONE_ID))
            dropzone = Dropzone.get_by_id(dropzone_key)
            dropzone.status = CLOSED
            ls = LoadStructure(dropzone_key)
            for load in ls.loads:
                if load.status in [WAITING, HOLD]:
                    ls.delete_load(load)
        else:
            dropzone = Dropzone.get_by_id(DEFAULT_DROPZONE_ID)

        Dropzone.put(dropzone)
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'active': 0,
            'dropzone_status': DROPZONE_STATUS
        }
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
        return


class ManageSales(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        message = {}
        sales = {}
        if user_data['user']:
            dropzone_key = int(self.request.get('dropzone'))
            dropzone = Dropzone.get_by_id(dropzone_key)
            jumper_key = int(self.request.get('jumper'))
            action = self.request.get('action')
            user = User.get_user(user_data['user'].email())
            if user.role in [ADMIN, SALES]:
                sales = SalesMega(dropzone_key, jumper_key)
                if action == 'fetch':
                    pass
                if action == 'add':
                    package_key = int(self.request.get('package'))
                    sales.sell(package_key)
                if action == 'delete':
                    pass
                template_values = {
                    'user_data': user_data,
                    'dropzone': dropzone,
                    'active': 3,
                    'dropzone_status': DROPZONE_STATUS,
                    'sales':sales.sales,
                    'message': message,
                    'jumper_key' : jumper_key,
                    'packages': SalesPackage.get_by_dropzone(dropzone_key),
                }
                template = JINJA_ENVIRONMENT.get_template('sales_list.html')
                self.response.write(template.render(template_values))
                return
            else:
                message.update({'title': "Cannot Sales"})
                message.update(
                    {'body': "You do not have Sales rights "})
                logging.log(logging.ERROR, message['body'])
        dropzone = DEFAULT_DROPZONE
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'active': 2,
            'dropzone_status': DROPZONE_STATUS,
        }
        message_header = json.dump(message)
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.headers.add('X-jump.tools-message',message_header)
        self.response.write(template.render(template_values))


class ManageLoads(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        dropzone_key = int(self.request.get('dropzone'))
        dropzone = Dropzone.get_by_id(dropzone_key)
        if user_data['user']:
            # GET PARAMETERS
            load_key = int(self.request.get('load', DEFAULT_LOAD_ID))
            action = self.request.get('action')
            message = {}
            user = User.get_user(user_data['user'].email())
            # Set the Dropone details
            dropzone_status = dropzone.status
            load_struct = LoadStructure(dropzone_key)
            # Set the Load Details
            if user.role in [ADMIN, MANIFEST]:
                if action == "takeoff":
                    load_struct.set_status(load_key, FLYING)
                if action == "add":
                    if dropzone_status == OPEN:
                        load_struct.add_load()
                    else:
                        message.update({'title': "Cannot Add"})
                        message.update(
                            {'body': dropzone.name + " is currently closed so new loads cannot be added "})
                if action == "landed":
                    load_struct.set_status(load_key, LANDED)
                if action == "hold":
                    load_struct.set_status(load_key, HOLD)
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
                logging.log(logging.ERROR, message['body'])

            # refresh loads
            loads = load_struct.loads
            slot_mega = load_struct.slot_mega
            template_values = {
                'user_data': user_data,
                'dropzone': dropzone,
                'loads': loads,
                'slot_mega': slot_mega,
                'slotsize': load_struct.freeslots(),
                'active': 1,
                'dropzone_status': DROPZONE_STATUS,
                'load_status': LOAD_STATUS,
                'load_colours': LOAD_COLOURS
            }
        else:
            template_values = {
                'user_data': user_data,
                'active': 1,
                'dropzone_status': DROPZONE_STATUS,
                'dropzone' : DEFAULT_DROPZONE,
            }
        message_header = json.dumps(message)
        self.response.headers.add('X-jump.tools-message', message_header)
        template = JINJA_ENVIRONMENT.get_template('loads.html')
        self.response.write(template.render(template_values))



class ManageManifest(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        message = {}
        if user_data['user']:
            # GET PARAMETERS
            dropzone_key = int(self.request.get('dropzone', DEFAULT_DROPZONE_ID))
            load_key = int(self.request.get('load', DEFAULT_LOAD_ID))
            action = self.request.get('action')
            jumper_key = int(self.request.get('jumper', "0"))
            user = User.get_user(user_data['user'].email())
            # Set the Dropone details
            dropzone = Dropzone.get_by_id(dropzone_key)
            registration = Registration.get_by_jumper(dropzone_key, jumper_key).get()
            # Set the Load Details
            load = Load.get_by_id(load_key)
            load_struct = LoadStructure(dropzone_key)
            if user.role in [ADMIN, MANIFEST]:
                message = load_struct.manifest_action(action,load, registration)
            else:
                message.update({'title': "Cannot Manifest"})
                message.update(
                    {'body': "You do not have Manifest rights "})
                logging.log(logging.ERROR, message['body'])
            #Refresh the Manifests
            slot_mega = load_struct.slot_mega
            slot_size = load_struct.freeslots()
            js=JumperStructure(dropzone_key)
            sales = SalesMega(dropzone_key, jumper_key)
            template_values = {
                'user_data': user_data,
                'dropzone': dropzone,
                'load': load,
                'slot_mega': slot_mega,
                'slotsize': slot_size,
                'jumpers': js.jumpers,
                'active': 1,
                'dropzone_status': DROPZONE_STATUS,
                'load_status': LOAD_STATUS,
                'load_colours': LOAD_COLOURS,
                'sales':sales.sales,
            }
        else:
            template_values = {
                'user_data': user_data,
                'active': 1,
                'dropzone_status': DROPZONE_STATUS,
                'dropzone': DEFAULT_DROPZONE,
            }
        message_header = json.dumps(message)
        self.response.headers.add('X-jump.tools-message', message_header)
        template = JINJA_ENVIRONMENT.get_template('manifest.html')
        self.response.write(template.render(template_values))


class ManageJumpers(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        message={}
        if user_data['user']:
            # GET PARAMETERS
            jumper_key = int(self.request.get('jumper', "0"))
            action = self.request.get('action')
            delete = self.request.get('delete')
            user = User.get_user(user_data['user'].email())
            dropzone_key = int(self.request.get('dropzone'))
            dropzone = Dropzone.get_by_id(dropzone_key)
            js = JumperStructure(dropzone_key)
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
                            logging.log(logging.ERROR, message['body'])
                        else:
                            js.add(jumper_key)
                    else:
                        message.update({'title': "Invalid Jumper"})
                        message.update(
                            {'body': "No Jumper registered with this email"})
                        logging.log(logging.ERROR, message['body'])

                if delete == "yes":
                    registration = Registration.get_by_jumper(dropzone_key, jumper_key).get()
                    if registration.current == NOT_CURRENT:
                        js.delete(jumper_key)
                    else:
                        message.update({'title': "Current Jumper"})
                        message.update({'body': "Cannot delete a current jumper. Make them uncurrent first"})
                        logging.log(logging.ERROR, message['body'])

                elif action == "update":
                    js.update(jumper_key,
                              datetime.datetime.strptime(self.request.get('waiver'),"%d/%m/%y"),
                              datetime.datetime.strptime(self.request.get('reserve'),"%d/%m/%y"),
                              int(self.request.get('current', "1")))
            else:
                message.update({'title': "Cannot Registration"})
                message.update(
                    {'body': "You do not have Registration rights "})
                logging.log(logging.ERROR, message['body'])

            # refresh registrations
            registrations = Registration.get_by_dropzone(dropzone_key).fetch()
            template_values = {
                'user_data': user_data,
                'dropzone': dropzone,
                'registration': registrations,
                'jumpers': js.jumpers,
                'active': 3,
                'dropzone_status': DROPZONE_STATUS,
                'registration_status': REGISTRATION_STATUS,
                'registration_colours': REGISTRATION_COLOURS,
            }
        else:
            template_values = {
                'user_data': user_data,
                'active': 1,
                'dropzone_status': DROPZONE_STATUS,
                'dropzone': DEFAULT_DROPZONE,
            }
        message_header = json.dumps(message)
        self.response.headers.add('X-jump.tools-message', message_header)
        template = JINJA_ENVIRONMENT.get_template('jumpers.html')
        self.response.write(template.render(template_values))


class ManageDz(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        message = {}
        if user_data['user']:
            user = User.get_user(user_data['user'].email())
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
                'user_roles': USER_ROLES,
                'role_colours': ROLE_COLOURS,
                'active': 4,
                'dropzone_status': DROPZONE_STATUS,
                'packages': SalesPackage.get_by_dropzone(dropzone_key),
                'request' : self.request.application_url,

            }
        else:
            template_values = {
                'user_data': user_data,
                'active': 1,
                'dropzone_status': DROPZONE_STATUS,
                'dropzone': DEFAULT_DROPZONE,
            }
            response = "index.html"
        message_header = json.dumps(message)
        self.response.headers.add('X-jump.tools-message', message_header)
        template = JINJA_ENVIRONMENT.get_template(response)
        self.response.write(template.render(template_values))
        return


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
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'users': User.get_by_dropzone(dropzone_key).fetch(),
            'user_roles': USER_ROLES,
            'role_colours': ROLE_COLOURS,
            'active': 4,
            'dropzone_status': DROPZONE_STATUS,
            'packages': SalesPackage.get_by_dropzone(dropzone_key),
            'request': self.request.application_url,

        }
        template = JINJA_ENVIRONMENT.get_template('configuredz.html')
        self.response.write(template.render(template_values))
        return


class UpdateUser(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = User.get_user(user_data['user'].email())
        dropzone_key = int(self.request.get('dropzone'))
        dropzone=Dropzone.get_by_id(dropzone_key)
        action = self.request.get('action')
        user_key = int(self.request.get('user', '-1'))
        if user.role == ADMIN:
            if action == "update":
                # GET PARAMETERS
                user_update = User.get_by_id(user_key)
                if user_update:
                    user_update.name = self.request.get('user_email')  + '@gmail.com'
                    user_update.role = int(self.request.get('user_role'))
                    user_update.dropzone = dropzone_key
                    user_update.put()
            if action == "add":
                name = 'new_user' + "@gmail.com"
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
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'users': User.get_by_dropzone(dropzone_key).fetch(),
            'user_roles': USER_ROLES,
            'role_colours': ROLE_COLOURS,
            'active': 4,
            'dropzone_status': DROPZONE_STATUS,
            'packages': SalesPackage.get_by_dropzone(dropzone_key),
            'request': self.request.application_url,

        }
        template = JINJA_ENVIRONMENT.get_template('configureuser.html')
        self.response.write(template.render(template_values))
        return


class UpdateSales(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = User.get_user(user_data['user'].email())
        dropzone_key = int(self.request.get('dropzone'))
        dropzone = Dropzone.get_by_id(dropzone_key)
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
                    name='new_package',
                    dropzone=dropzone_key,
                    size=0
                )
                package.put()
            if action == "delete":
                package = SalesPackage.get_by_id(package_key)
                if package:
                    package.key.delete()
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'users': User.get_by_dropzone(dropzone_key).fetch(),
            'user_roles': USER_ROLES,
            'role_colours': ROLE_COLOURS,
            'active': 4,
            'dropzone_status': DROPZONE_STATUS,
            'packages': SalesPackage.get_by_dropzone(dropzone_key),
            'request': self.request.application_url,

        }
        template = JINJA_ENVIRONMENT.get_template('configuresales.html')
        self.response.write(template.render(template_values))
        return

class RetimeLoads(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = User.get_user(user_data['user'].email())
        message = {}
        load_key = int(self.request.get('load', DEFAULT_LOAD_ID))
        action = self.request.get('action')
        dropzone_key = int(self.request.get('dropzone'))
        dropzone = Dropzone.get_by_id(dropzone_key)
        if user.role in [ADMIN, MANIFEST]:
            load_struct = LoadStructure(dropzone_key)
            if action == "5":
                load_struct.retime_load(load_key, 5)
            if action == "10":
                load_struct.retime_load(load_key, 10)
            if action == "select":
                load_struct.retime_load(load_key, 0)

        else:
            message.update({'title': "Cannot Manifest"})
            message.update(
                {'body': "You do not have Manifest rights "})
            logging.log(logging.ERROR, message['body'])

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
        message_header = json.dumps(message)
        self.response.headers.add('X-jump.tools-message', message_header)
        template = JINJA_ENVIRONMENT.get_template('loads.html')
        self.response.write(template.render(template_values))

class NewDz(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = User.get_user(user_data['user'].email())
        if user:
            dropzone = Dropzone(name="New Dropzone",
                                default_load_time=0,
                                default_load_number=0,
                                default_slot_number=0,
                                status=CLOSED,
                                tag="",
                                kiosk_cols=1,
                                kiosk_rows=1, )
            dropzone.put()
            user.dropzone = dropzone.key.id()
            user.role = ADMIN
            user.put()
        else:
            dropzone = DEFAULT_DROPZONE
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'active': 0,
            'dropzone_status': DROPZONE_STATUS
        }
        message = {
            'title': 'New Dropzone Created',
            'body' : 'New dropzone has been created and linked to this user. Go to Congfigure / Dropzone Config to change the name and details',
        }
        message_header = json.dumps(message)
        self.response.headers.add('X-jump.tools-message', message_header)
        template = JINJA_ENVIRONMENT.get_template('manage.html')
        self.response.write(template.render(template_values))
        return


class SideBar(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = user_data['user']
        if user:
            # Get the dropzone details based on the user
            dropzone_key = User.get_user(user.email()).dropzone
            dropzone = Dropzone.get_by_id(dropzone_key)
            js=JumperStructure(dropzone_key)
            load_key = self.request.get('load')
            if load_key != "":
                load_key=int(self.request.get('load'))
            else:
                load=0
        else:
            dropzone = DEFAULT_DROPZONE
        side_bar = self.request.get('side_bar')
        case_type = {
            'index':'index_sb.html',
            'load':'load_sb.html',
            'jumper':'jumpers_sb.html',
            'configuredz': 'configuredz_sb.html',
            'sales' : 'sales_sb.html',
            'users': 'users_sb.html',
            'none': 'none.html',
            'manifest': 'manifest_sb.html',
        }
        if side_bar in case_type:
            response = case_type[side_bar]
        else:
            return
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'active': 0,
            'dropzone_status': DROPZONE_STATUS,
            'jumpers': js.jumpers,
            'load': load_key,
        }
        template = JINJA_ENVIRONMENT.get_template(response)
        self.response.write(template.render(template_values))
        return

class DzStat(webapp2.RequestHandler):
    def post(self):
        dropzone = Dropzone.get_by_id(int(self.request.get('dropzone')))
        response = json.dumps({
            'status': DROPZONE_STATUS[dropzone.status],
            'colour': DROPZONE_COLOURS[dropzone.status],
        })
        self.response.write(response)
