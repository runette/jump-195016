    #!/usr/bin/env python
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
            dropzone= Dropzone.get_by_id(dropzone_key)
        else:
            dropzone = Dropzone(
                                name = DEFAULT_DROPZONE_NAME,
                                status = DROPZONE_CLOSED
            )

        template_values = {
            'user_data' : user_data,
            'dropzone': dropzone,
        }
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class StartDay (webapp2.RequestHandler):

    def get(self):
        user_data = UserStatus(self.request.uri)
        dropzone_key = int(self.request.get('dropzone', DEFAULT_DROPZONE_ID))
        dropzone = Dropzone.get_by_id(dropzone_key)
        dropzone.status = DROPZONE_OPEN
        Dropzone.put(dropzone)
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,

        }
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class EndDay (webapp2.RequestHandler):
    def get(self):
        user_data = UserStatus(self.request.uri)
        dropzone_key = int(self.request.get('dropzone',DEFAULT_DROPZONE_ID))
        dropzone = Dropzone.get_by_id(dropzone_key)
        dropzone.status = DROPZONE_CLOSED
        loads = Load.get_loads(dropzone_key)
        for load in loads :
            if load.status == LOAD_STATUS[0] or load.status == LOAD_STATUS[2] :
                DeleteLoad(load)
        Dropzone.put(dropzone)
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
        }
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class ManageSales (webapp2.RequestHandler):
    def get(self):
        user_data = UserStatus(self.request.uri)

        dropzone_key = int(self.request.get('dropzone',DEFAULT_DROPZONE_ID))
        dropzone = Dropzone.get_by_id(dropzone_key)

        template_values = {
            'user_data': user_data,
            'dropzone': dropzone
        }
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class ManageLoads (webapp2.RequestHandler):
    def get(self):
        user_data = UserStatus(self.request.uri)
        user = user_data['user']
        # GET Parameters
        dropzone_key = int(self.request.get('dropzone',DEFAULT_DROPZONE_ID))
        # Get Dropzone details
        dropzone = Dropzone.get_by_id(dropzone_key)
        #Get loads
        loads = Load.get_loads(dropzone_key).fetch()
        slot_mega = LoadStructure(loads)


        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'loads' : loads,
            'slot_mega' : slot_mega,
            'slotsize': FreeSlots(loads, slot_mega, dropzone.defaultloadnumber),

        }
        template = JINJA_ENVIRONMENT.get_template('loads.html')
        self.response.write(template.render(template_values))



class LoadAction (webapp2.RequestHandler ) :
    def get(self):
        user_data = UserStatus(self.request.uri)
        # GET PARAMETERS
        dropzone_key = int(self.request.get('dropzone',DEFAULT_DROPZONE_ID))
        load_key = int(self.request.get('load',DEFAULT_LOAD_ID))
        action = self.request.get('action')
        message = {}
        # Set the Dropone details
        dropzone = Dropzone.get_by_id(dropzone_key)
        dropzone_status = dropzone.status
        # Set the Load Details
        loads = Load.get_loads(dropzone_key).fetch()
        if action == "takeoff" :
            load = Load.get_by_id(load_key)
            load.status = LOAD_STATUS[1]
            load.put()
        if action == "add" :
            if dropzone_status == DROPZONE_OPEN:
                last = len(loads) - 1
                time_increment = datetime.timedelta(minutes=dropzone.defaultloadtime)
                if last >= 0 :
                    load = Load(number =loads[last].number + 1,
                                slots = dropzone.defaultloadnumber,
                                precededby = loads[last].key.id(),
                                status = LOAD_STATUS[0],
                                time = (datetime.datetime.combine(datetime.date(1,1,1),loads[last].time) + time_increment).time(),
                                dropzone = dropzone_key
                                )
                    load.put()
                else :
                    load = Load(
                         number = 1,
                        slots=dropzone.defaultloadnumber,
                        precededby=-1,
                        status=LOAD_STATUS[0],
                        time=(datetime.datetime.now() + time_increment).time(),
                        dropzone=dropzone_key
                        )
                    load.put()
            else :
                message.update({'title': "Cannot Add"})
                message.update(
                    {'body': dropzone.name + " is currently closed so new loads cannot be added "})

        if action == "landed" :
            load = Load.get_by_id(load_key)
            load.status = LOAD_STATUS[3]
            load.put()
        if action == "hold":
            load = Load.get_by_id(load_key)
            load.status = LOAD_STATUS[2]
            load.put()

        #refresh loads
        loads = Load.get_loads(dropzone_key).fetch()
        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'loads' : loads,
            'slot_mega' : LoadStructure(loads),
            'message' : message
        }
        template = JINJA_ENVIRONMENT.get_template('loads.html')
        self.response.write(template.render(template_values))

class ManageManifest(webapp2.RequestHandler) :
    def get(self):
        user_data = UserStatus(self.request.uri)
        # GET PARAMATERS
        dropzone_key = int(self.request.get('dropzone', DEFAULT_DROPZONE_ID))
        load_key = int(self.request.get('load', DEFAULT_LOAD_ID))
        # Set the Dropone details
        dropzone = Dropzone.get_by_id(dropzone_key)
        # Set the Load Details
        load = Load.get_by_id(load_key)
        loads = [load]
        slot_mega = LoadStructure(loads)


        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'load': load,
            'slot_mega': slot_mega,
            'slotsize' : FreeSlots(loads, slot_mega, dropzone.defaultloadnumber),
            'jumpers' : JumperStructure(dropzone_key)
        }
        template = JINJA_ENVIRONMENT.get_template('manifest.html')
        self.response.write(template.render(template_values))

class ManifestAction(webapp2.RequestHandler) :
    def get(self):
        user_data = UserStatus(self.request.uri)
        # GET PARAMETERS
        dropzone_key = int(self.request.get('dropzone', DEFAULT_DROPZONE_ID))
        load_key = int(self.request.get('load', DEFAULT_LOAD_ID))
        action = self.request.get('action')
        jumper_key = int(self.request.get('jumper'))
        message = {}
        # Set the Dropone details
        dropzone = Dropzone.get_by_id(dropzone_key)

        # Set the Load Details
        load = Load.get_by_id(load_key)
        loads = [load]
        slot_mega = LoadStructure(loads)
        slot_size = FreeSlots(loads, slot_mega, dropzone.defaultloadnumber)
        if action == "add" :
            if load.status in [LOAD_STATUS[0],LOAD_STATUS[2]]:
                if slot_size[load.key.id()] > 0 :
                    manifest = Manifest(
                        load = load_key,
                        jumper = jumper_key
                    )
                    manifest.put()

                else :
                    message.update({'title': "No Slots"})
                    message.update({'body': "You cannot manifest on this load - there are no slots left"})
            else :
                message.update({'title':"Cannot Add"})
                message.update({'body':"This Load is not Open for Manifest. The Load status is \" " + load.status + "\""})

        template_values = {
            'user_data': user_data,
            'dropzone': dropzone,
            'load': load,
            'slot_mega': LoadStructure(loads),
            'slotsize':  FreeSlots(loads, slot_mega, dropzone.defaultloadnumber),
            'jumpers': JumperStructure(dropzone_key),
            'message' : message
        }
        template = JINJA_ENVIRONMENT.get_template('manifest.html')
        self.response.write(template.render(template_values))


class ManageJumpers(webapp2.RequestHandler) :
    a =1



app = webapp2.WSGIApplication([
        ('/', MainPage),
        ('/loads' , ManageLoads),
        ('/startday' , StartDay),
        ('/endday' , EndDay),
        ('/sales' , ManageSales),
        ('/manifest' , ManageManifest),
        ('/loadaction' , LoadAction),
        ('/manifestaction' , ManifestAction),
        ('/jumpers' , ManageJumpers)

], debug=True)
