<!--Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)-->
<!--SPDX-License-Identifier: 0BSD-->
# Login for Local Encryption

**Situation and Problems.** An application maintains sensible information for which you want to apply access restrictions, not relying on a particular operating system setup. Additionally, the application may need server access but you do not want to expose the credentials to the user. In both case, you also do not want to store this information on disk without encryption.

**Feature.** Upon first usage, the user sets a password and the application requires the password to run. APPXF maintains a symmetric encryption key with this password and enables a secure storage.

## Old Security Documentation
Your application likely stores sensible data like passwords to servers or details on other persons. A **login** procedure allows to encrypt the locally stored data. You thereby do not depend on the password protection of the operating system and stolen data cannot be used without this password. A **registration** procedure can ensure that only authorized users get access to servers. For example can you verify the requested user role and you can provide server passwords as part of the registration process.

Usage can be as simple as the following. Note that login and registration both requiere a appxf configuration object (see TBD):
```python
from appxf import config, login, registration

# You should always use your own salt for your tool but never change it, unless
# you want user passwords to become invalid.
security = Security(salt = 'PickYourOwnSaltForYourApplication!')

login = Login(security)
login.check()
# Note: If login procedure fails (password not correct), code will end here
# with an exception.

# Login is required before registration, but registration is optional.
registration = Registration(security)
registration.check()
# Note: Like with login, code will end with an Exception if registration check
# failed.

# After this step, securily stored data can be loaded (like Config section
# (see link TBD))
```
### Login
Without a gui, this could be like
```python
from appxf.security.local import Security

# You need to get the password input from somewhere, appxf does not support a
# command line helper.
pwd = ''

# You need to create a security context. You should define __your salt string__
# for __your application__. You __can__ change the storage for the security
# module.
security = Security(salt = 'PickYourOwnSaltForYourApplication!', storage = './data/security')

# If not yet initialized, you take the initial password to setup the security
# context. There won't be any data stored, so no further check needed.
if security.is_user_initialized():
	security.unlock_user(pwd)
# The above will throw an exception if the password is not correct.
else:
	security.init_user(pwd)
# There is no need to provide the password anymore. The user will be
# unlocked.
```

Dropping images:
`![login](securityLogin.png)`