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

import os
import webapp2
import jinja2
import datetime
from data import *

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


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

        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
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
            dropzone.status = DROPZONE_OPEN
            Dropzone.put(dropzone)
            for i in range(dropzone.defaultloadnumber):
                loads = Load.get_loads(dropzone_key).fetch()
                Load.add_load(loads, dropzone_key).put()

        else:
            dropzone = Dropzone.get_by_id(DEFAULT_DROPZONE_ID)

        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,

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
            dropzone.status = DROPZONE_CLOSED
            loads = Load.get_loads(dropzone_key).fetch()
        else:
            dropzone = Dropzone.get_by_id(DEFAULT_DROPZONE_ID)
            loads = []
        for load in loads:
            if load.status == LOAD_STATUS[0] or load.status == LOAD_STATUS[2]:
                DeleteLoad(load)
        Dropzone.put(dropzone)
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
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
            'dropzone': dropzone
        }
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class ManageLoads(webapp2.RequestHandler):
    def get(self):
        user_data = UserStatus(self.request.uri)
        # GET PARAMETERS
        dropzone_key = int(self.request.get('dropzone', DEFAULT_DROPZONE_ID))
        load_key = int(self.request.get('load', DEFAULT_LOAD_ID))
        action = self.request.get('action')
        message = {}
        # Set the Dropone details
        dropzone = Dropzone.get_by_id(dropzone_key)
        dropzone_status = dropzone.status
        # Set the Load Details
        loads = Load.get_loads(dropzone_key).fetch()
        if action == "takeoff":
            load = Load.get_by_id(load_key)
            load.status = LOAD_STATUS[1]
            load.put()
        if action == "add":
            if dropzone_status == DROPZONE_OPEN:
                Load.add_load(loads, dropzone_key).put()
            else:
                message.update({'title': "Cannot Add"})
                message.update(
                    {'body': dropzone.name + " is currently closed so new loads cannot be added "})
        if action == "landed":
            load = Load.get_by_id(load_key)
            load.status = LOAD_STATUS[3]
            load.put()
        if action == "hold":
            load = Load.get_by_id(load_key)
            load.status = LOAD_STATUS[2]
            load.put()

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
        if jumper_key:
            jumper_key = int(jumper_key)
        # Set the Dropone details
        dropzone = Dropzone.get_by_id(dropzone_key)

        # Set the Load Details

        load = Load.get_by_id(load_key)
        loads = [load]
        slot_mega = LoadStructure(loads)
        slot_size = FreeSlots(loads, slot_mega, dropzone_key)
        if action == "add":
            if load.status in [LOAD_STATUS[0], LOAD_STATUS[2]]:
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
                    {'body': "This Load is not Open for Manifest. The Load status is \" " + load.status + "\""})

        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'load': load,
            'slot_mega': LoadStructure(loads),
            'slotsize': FreeSlots(loads, slot_mega, dropzone_key),
            'jumpers': JumperStructure(dropzone_key),
            'message': message
        }
        template = JINJA_ENVIRONMENT.get_template('manifest.html')
        self.response.write(template.render(template_values))


class ManageJumpers(webapp2.RequestHandler):
    a = 1


class ManageDz(webapp2.RequestHandler):
    def get(self):
        user_data = UserStatus(self.request.uri)
        user = user_data['user']
        if user:
            # Get the dropzone details based on the user
            dropzone_key = User.get_user(user.email()).fetch()[0].dropzone
            dropzone = Dropzone.get_by_id(dropzone_key)
        else:
            dropzone = Dropzone.get_by_id(DEFAULT_DROPZONE_ID)

        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
        }
        template = JINJA_ENVIRONMENT.get_template('configuredz.html')
        self.response.write(template.render(template_values))


class UpdateDz(webapp2.RequestHandler):
    def post(self):
        user_data = UserStatus(self.request.uri)
        user = user_data['user']
        if user:
            # GET PARAMETERS
            dropzone_key = int(self.request.get('dropzone'))
            dropzone = Dropzone.get_by_id(dropzone_key)
            dropzone.name = self.request.get('dropzone_name')
            dropzone.defaultslotnumber = int(self.request.get('default_slot_number'))
            dropzone.defaultloadnumber = int(self.request.get('default_load_number'))
            dropzone.defaultloadtime = int(self.request.get('default_load_time'))
            dropzone.put()
            self.redirect('/')

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
    ('/updatedz', UpdateDz)

], debug=True)
