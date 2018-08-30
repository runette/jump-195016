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

class Kiosk (webapp2.RequestHandler):
    def get(self):
        # GET PARAMETERS
        dropzone_key = int(self.request.get('dropzone', DEFAULT_DROPZONE_ID))
        # Set the Dropzone details
        dropzone = Dropzone.get_by_id(dropzone_key)

        if dropzone.kiosk_rows:
            slice_size = dropzone.kiosk_rows
        else:
            slice_size = DEFAULT_SLICE_SIZE
        if dropzone.kiosk_cols:
            load_len = dropzone.kiosk_cols
        else:
            load_len = DEFAULT_KIOSK_NUMBER_OF_COLUMNS

        if dropzone:
            load_struct = LoadStructure(dropzone_key)
        else:
            dropzone = Dropzone.get_by_id(DEFAULT_DROPZONE_ID)
            load_struct = LoadStructure(DEFAULT_DROPZONE_ID)
        loads = load_struct.loads
        slot_mega = load_struct.slot_mega
        next_loads = []
        for load in loads:
            if load.status == LANDED:
                continue
            else:
                next_loads.append(load)
        load_len = min(len(next_loads), load_len)

        template_values = {
            'dropzone': dropzone,
            'next_loads': next_loads,
            'slot_mega': slot_mega,
            'slotsize': load_struct.freeslots(),
            'load_len': load_len,
            'slice': slice_size,
            'dropzone_status': DROPZONE_STATUS,
            'load_status': LOAD_STATUS,
            'load_colours': LOAD_COLOURS,
        }

        template = JINJA_ENVIRONMENT.get_template('kiosk.html')
        self.response.write(template.render(template_values))

class UpdateKiosk(webapp2.RequestHandler):
    def post(self):
        dropzone_key = int(self.request.get('dropzone'))
        dropzone = Dropzone.get_by_id(dropzone_key)
        dropzone.kiosk_cols = int(self.request.get('cols', str(DEFAULT_KIOSK_NUMBER_OF_COLUMNS)))
        dropzone.kiosk_rows = int(self.request.get('rows', str(DEFAULT_SLICE_SIZE)))
        dropzone.put()
        self.redirect('/configdz?dropzone=' + str(dropzone_key) + '&action=kiosk')
