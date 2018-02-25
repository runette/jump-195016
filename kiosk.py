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
import urllib
import webapp2
import jinja2
from google.appengine.ext import ndb
from google.appengine.api import users
import datetime
import main


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

# [END Imports]

#[START Global variables]



#[END Global variables]

class Kiosk (webapp2.RequestHandler):
    a=1


app = webapp2.WSGIApplication([
        ('/kiosk', Kiosk),


], debug=True)