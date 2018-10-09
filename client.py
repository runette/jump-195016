#!/usr/bin/env python
#  Copyright 2018 Paul Harwood
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
from data import *


# [END Imports]

# [START Global variables]


#[END Global variables]

class Client (webapp2.RequestHandler):
    def get(self):
        # GET PARAMETERS
        user_data = UserStatus(self.request.uri)
        user = user_data['user']
        message = {}
        if not user:
            message.update({'title': "Not logged in"})
            message.update({'body': "You are not logged in"})
            reg_mega = {}
        template_values = {
            'user_data': user_data,
            'message': message,

        }
        template = JINJA_ENVIRONMENT.get_template('client.html')
        self.response.write(template.render(template_values))

    def post(self):
        pass
        return

class ClientDz (webapp2.RequestHandler):
    def post(self):
        # GET PARAMETERS
        user_data = UserStatus(self.request.uri)
        user = user_data['user']
        message = {}
        if user:
            rm = RegMega(user)
            reg_mega = rm.reg_mega
        else:
            message.update({'title': "Not logged in"})
            message.update({'body': "You are not logged in"})
            reg_mega = {}
        template_values = {
            'message': message,
            'reg_mega': reg_mega,
            'registration_status': REGISTRATION_STATUS,
            'registration_colours': REGISTRATION_COLOURS,
            'dropzone_status': DROPZONE_STATUS,
        }
        template = JINJA_ENVIRONMENT.get_template('clientdz.html')
        self.response.write(template.render(template_values))


class ClientConfig (webapp2.RequestHandler) :
    def post(self):
        # GET PARAMETERS
        user_data = UserStatus(self.request.uri)
        message = {}
        action = self.request.get('action')
        user = user_data['user']
        if user:
            jumper = Jumper.get_by_gid(user.user_id()).get()
            if action == "update" :
                # if jumper.google_id == user.user_id :
                    jumper.name = self.request.get('name')
                    jumper.email = self.request.get('email')
                    jumper.put()
        else:
            jumper = ""
            message.update({'title': "Not logged in"})
            message.update({'body': "You are not logged in"})
        template_values = {
            'user_data': user_data,
            'jumper' : jumper,
            'message' : message,
        }
        template = JINJA_ENVIRONMENT.get_template('clientconfig.html')
        self.response.write(template.render(template_values))


class ClientManifest(webapp2.RequestHandler) :
    def post(self):
        user_data = UserStatus(self.request.uri)
        message = {}
        dropzone_key = int(self.request.get("dropzone"))
        user = user_data['user']
        if user:
            rm = RegMega(user)
            dropzone = Dropzone.get_by_id(dropzone_key)
            registration = Registration.get_by_jumper(dropzone_key,rm.jumper).get()
            load_struct = LoadStructure(dropzone_key)
            jumper = Jumper.get_by_id(rm.jumper)
            slots = []
            for load in load_struct.loads:
                if jumper in load_struct.slot_mega[load.key.id()]:
                    slots.append(load.key.id())
            template_values = {
                'user_data': user_data,
                'message' : message,
                'dropzone': dropzone,
                'registration':registration,
                'registration_status' : REGISTRATION_STATUS,
                'registration_colours' : REGISTRATION_COLOURS,
                'dropzone_status': DROPZONE_STATUS,
                'loads': load_struct.loads,
                'slots' : slots,
                'load_colours': LOAD_COLOURS,
                'load_status': LOAD_STATUS,
                'slotsize': load_struct.freeslots(),
            }
        else:
            message.update({'title': "Not logged in"})
            message.update({'body': "You are not logged in"})
            template_values = {
                'user_data': user_data,
                'message' : message,
            }
        template = JINJA_ENVIRONMENT.get_template('clientmanifest.html')
        self.response.write(template.render(template_values))

class ClientLoads(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        message = {}
        dropzone_key = int(self.request.get("dropzone"))
        user = user_data['user']
        if user:
            rm = RegMega(user)
            dropzone = Dropzone.get_by_id(dropzone_key)
            registration = Registration.get_by_jumper(dropzone_key, rm.jumper).get()
            load_struct = LoadStructure(dropzone_key)
            jumper = Jumper.get_by_id(rm.jumper)
            load = Load.get_by_id(int(self.request.get('load')))
            sm = SalesMega(dropzone_key,jumper.key.id())
            action = self.request.get('action')
            if action:
                message = load_struct.manifest_action(action, load, registration)
        else:
            message.update({'title': "Not logged in"})
            message.update({'body': "You are not logged in"})
        template_values = {
            'user_data': user_data,
            'message': message,
            'dropzone': dropzone,
            'registration': registration,
            'registration_status': REGISTRATION_STATUS,
            'registration_colours': REGISTRATION_COLOURS,
            'dropzone_status': DROPZONE_STATUS,
            'load': load,
            'slots': load_struct.slot_mega[load.key.id()],
            'load_colours': LOAD_COLOURS,
            'load_status': LOAD_STATUS,
            'slotsize': load_struct.freeslots(),
            'sales' : sm.sales,
        }
        template = JINJA_ENVIRONMENT.get_template('clientload.html')
        self.response.write(template.render(template_values))
        return

class ClientActions(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = user_data['user']
        if user:
            dropzone_key = int(self.request.get("dropzone"))
            load_key= int(self.request.get('load'))
            action = self.request.get('action')
            rm = RegMega(user)
            registration = Registration.get_by_jumper(dropzone_key, rm.jumper).get()
            # Set the Load Details
            load = Load.get_by_id(load_key)
            load_struct = LoadStructure(dropzone_key)
            message = load_struct.manifest_action(action, load, registration)
        return self.redirect(self.request.referer)

class ClientAccount(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = user_data['user']
        if user:
            dropzone_key = int(self.request.get("dropzone"))
            dropzone = Dropzone.get_by_id(dropzone_key)
            rm = RegMega(user)
            registration = Registration.get_by_jumper(dropzone_key, rm.jumper).get()
            jumper = Jumper.get_by_id(rm.jumper)
            jumper_key = jumper.key.id()
            sales = SalesMega(dropzone_key, jumper_key)
            template_values = {
                'user_data': user_data,
                'dropzone': dropzone,
                'active': 3,
                'dropzone_status': DROPZONE_STATUS,
                'sales': sales.sales,
                'jumper_key': jumper_key,
                'packages': SalesPackage.get_by_dropzone(dropzone_key),
                'registration': registration,
                'registration_status': REGISTRATION_STATUS,
                'registration_colours': REGISTRATION_COLOURS,
            }
        else:
            dropzone = DEFAULT_DROPZONE
            template_values = {
                'user_data': user_data,
                'dropzone': dropzone,
                'active': 3,
                'dropzone_status': DROPZONE_STATUS,
            }
        template = JINJA_ENVIRONMENT.get_template('clientaccount.html')
        self.response.write(template.render(template_values))
        return

class ClientLogbook(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = user_data['user']
        if user:
            rm = RegMega(user)
            jumper = Jumper.get_by_id(rm.jumper)
            jumper_key = jumper.key.id()
            logbook = Log(jumper_key)
            template_values = {
                'user_data': user_data,
                'active': 2,
                'logbook': logbook.logbook,
            }
        else:
            dropzone = DEFAULT_DROPZONE
            template_values = {
                'user_data': user_data,
                'active': 2,
            }
        template = JINJA_ENVIRONMENT.get_template('clientlogbook.html')
        self.response.write(template.render(template_values))
        return

