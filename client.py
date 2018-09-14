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
        message = {}
        reg_mega=[]
        if user_data:
            user = user_data['user']
            jumper = Jumper.get_by_gid(user.user_id()).get()
            if jumper:
                jumper = Jumper.get_by_gid(user.user_id()).get()
                registrations = Registration.get_all_by_jumper(jumper.key.id())
                for registration in registrations:
                    reg_mega.append((registration, Dropzone.get_by_id(registration.dropzone)))
            else:
                jumper = Jumper(
                    name=user.nickname(),
                    email=user.email(),
                    google_id=user.user_id(),
                )
                jumper.put()
        else:
            message.update({'title': "Not logged in"})
            message.update({'body': "You are not logged in"})
        template_values = {
            'user_data': user_data,
            'message': message,
            'reg_mega': reg_mega,
            'registration_status': REGISTRATION_STATUS,
            'registration_colours': REGISTRATION_COLOURS,
        }
        template = JINJA_ENVIRONMENT.get_template('clientdz.html')
        self.response.write(template.render(template_values))


class ClientConfig (webapp2.RequestHandler) :
    def get(self):
        # GET PARAMETERS
        user_data = UserStatus(self.request.uri)
        message = {}
        action = self.request.get('action')
        if user_data :
            user = user_data['user']
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
    def get(self):
        user_data = UserStatus(self.request.uri)
        message = {}
        if user_data:
            user = user_data['user']
            jumper = Jumper.get_by_gid(user.user_id()).get()
            registrations = Registration.get_all_by_jumper(jumper.key.id())
            reg_mega = []
            for registration in registrations :
                reg_mega.append((registration,Dropzone.get_by_id(registration.dropzone)))
        else :
            message.update({'title': "Not logged in"})
            message.update({'body': "You are not logged in"})
        template_values = {
            'user_data': user_data,
            'message' : message,
            'reg_mega' : reg_mega,
            'registration_status' : REGISTRATION_STATUS,
            'registration_colours' : REGISTRATION_COLOURS,
        }
        template = JINJA_ENVIRONMENT.get_template('clientdz.html')
        self.response.write(template.render(template_values))

