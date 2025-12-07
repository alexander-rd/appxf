from kiss_cf.gui import KissApplication, Login
from kiss_cf.security import Security, SecurePrivateStorage
from kiss_cf.storage import LocalStorage
from kiss_cf.config import Config

# Initialize security for user password and credentials handling
security = Security(
    salt='APPXF Template',
    file='./security')

# Configuration setup using secured storage
config_storage_factory = SecurePrivateStorage.get_factory(
    base_storage_factory=LocalStorage.get_factory(path='./config'),
    security=security)
config = Config(default_storage_factory=config_storage_factory)
config.add_section(
    'USER', settings = {
        'Email': 'Email',
    })
config.add_section(
    'BACKEND', settings = {
        'URL': 'String',
        'Password': 'Password',
    })

# Handle the user login. Succesful login is required to load the secured
# configuration data.
login = Login(
    security=security,
    user_config=config.section('USER'),
    app_name='APPXF Login Template')
login.check()
config.load()

# run application main window
app = KissApplication()
app.mainloop()