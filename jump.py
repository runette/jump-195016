import webapp2
from manage import *
from kiosk import *
from client import *


app = webapp2.WSGIApplication([
    webapp2.Route ('/', handler= MainPage),
    webapp2.Route ('/manage', handler=MainPage),
    webapp2.Route ('/loads', handler=ManageLoads),
    webapp2.Route ('/startday', handler=StartDay),
    webapp2.Route ('/endday', handler=EndDay),
    webapp2.Route ('/sales', handler=ManageSales),
    webapp2.Route ('/manifest', handler=ManageManifest),
    webapp2.Route ('/loadaction', handler=ManageLoads),
    webapp2.Route ('/manifestaction', handler=ManageManifest),
    webapp2.Route ('/jumpers', handler=ManageJumpers),
    webapp2.Route ('/configdz', handler=ManageDz),
    webapp2.Route ('/updatedz', handler=UpdateDz),
    webapp2.Route ('/newdz', handler=NewDz),
    webapp2.Route ('/updateuser', handler=UpdateUser),
    webapp2.Route ('/retime', handler=RetimeLoads),
    webapp2.Route ('/updatesales', handler=UpdateSales),
    webapp2.Route ('/kiosk', handler=Kiosk),
    webapp2.Route ('/kiosk/update', handler=UpdateKiosk),
    webapp2.Route ('/client', handler=Client),
    webapp2.Route ('/client_dz', handler=ClientDz),
    webapp2.Route ('/client/manifest', handler=ClientManifest),
    webapp2.Route ('/client/account', handler=ClientAccount),
    webapp2.Route ('/client/config', handler=ClientConfig),
    webapp2.Route ('/client/load', handler=ClientLoads),
    webapp2.Route ('/client/logbook', handler=ClientLogbook),
], debug=True)

