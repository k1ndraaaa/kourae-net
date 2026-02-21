from flask import * #type:ignore

from microapps.mnt.MainClass import Mnt
from microapps.auth.MainClass import AuthManager
from native.LogManager.MainClass import LogManager
from native.EnvManager.MainClass import EnvManager


mnt = Mnt()
auth_manager = AuthManager()
environment = EnvManager()
log_manager = LogManager()

mnt.init_adapters()
auth_manager.init_adapters()
auth_manager.init_adapters()
log_manager.init_adapters()

app = Flask(__name__) #type:ignore

environment.mapApplications(
    app=app, 
    logmanager=log_manager, 
    authmanager=auth_manager,
    mntmicroapp=mnt
)

if __name__:
    app.run(debug=True, host="0.0.0.0", port=5000)