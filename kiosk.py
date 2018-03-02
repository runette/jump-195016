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


    import webapp2
from data import *

    # [END Imports]

    # [START Global variables]


#[END Global variables]

class Kiosk (webapp2.RequestHandler):
    def get(self):
        # GET PARAMETERS
        dropzone_key = int(self.request.get('dropzone', DEFAULT_DROPZONE_ID))
        # Set the Dropzone details
        dropzone = Dropzone.get_by_id(dropzone_key)

        if dropzone:
            loads = Load.get_loads(dropzone_key).fetch()
            slot_mega = LoadStructure(loads)
            next_loads = []
            for load in loads:
                if load.status == LANDED:
                    continue
                else:
                    next_loads.append(load)
        else:
            dropzone = Dropzone.get_by_id(DEFAULT_DROPZONE_ID)
            loads = Load.get_loads(DEFAULT_DROPZONE_ID).fetch()
        load_len = min(len(next_loads), KIOSK_NUMBER_OF_COLUMNS)

        template_values = {
            'dropzone': dropzone,
            'next_loads': next_loads,
            'slot_mega': slot_mega,
            'slotsize': FreeSlots(loads, slot_mega, dropzone_key),
            'load_len': load_len,
            'slice': SLICE_SIZE,
            'dropzone_status': DROPZONE_STATUS,
            'load_status': LOAD_STATUS
        }

        template = JINJA_ENVIRONMENT.get_template('kiosk.html')
        self.response.write(template.render(template_values))



app = webapp2.WSGIApplication([
        ('/kiosk', Kiosk),


], debug=True)