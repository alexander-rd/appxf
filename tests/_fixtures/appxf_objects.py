''' Helper functions to generate dummy APPXF objects for testing
'''

import os

from kiss_cf.storage import LocalStorage, RamStorage
from kiss_cf.security import Security, SecurityMock
from kiss_cf.registry import Registry
from kiss_cf.config import Config

### Config Objects
# Note that Config implementation uses RamStorage if no StorageFactory is
# provided.
def get_dummy_config() -> Config:
    return Config()

def get_dummy_user_config() -> Config:
    config = get_dummy_config()
    config.add_section(section='USER')
    return config

### Security Objects
def get_security(path: str | None = None) -> Security:
    if path is None:
        # use security mock
        sec = SecurityMock()
    else:
        sec = Security(
            salt='test',
            file=os.path.join(path, 'user'))
    return sec

def get_security_initialized(
        path: str | None = None,
        password: str = 'password') -> Security:
    sec = get_security(path)
    if not sec.is_user_initialized():
        sec.init_user(password)
    # we have to regenerate the security object since it is unlocked after use
    # init
    del sec
    return get_security(path)

def get_security_unlocked(
        path: str | None = None,
        password: str = 'password') -> Security:
    sec = get_security_initialized(path, password)
    sec.unlock_user(password)
    return sec

def get_fresh_registry(security: Security,
                       config: Config,
                       path: str | None = None,
                       local_name: str = 'local_registry',
                       remote_name: str = 'remote_registry'
                       ) -> Registry:
    if path is None:
        local_storage_factory=RamStorage.get_factory(
            ram_area=local_name)
        remote_storage_factory=RamStorage.get_factory(
            ram_area=remote_name)
    else:
        local_storage_factory=LocalStorage.get_factory(
            path=os.path.join(path, local_name))
        remote_storage_factory=LocalStorage.get_factory(
            path=os.path.join(path, remote_name))
    reg = Registry(
        local_storage_factory=local_storage_factory,
        remote_storage_factory=remote_storage_factory,
        security=security,
        config=config
        )
    return reg

def get_registry_admin_initialized(path: str,
                                   security: Security,
                                   config: Config,
                                   local_name: str = 'local_registry',
                                   remote_name: str = 'remote_registry'
                                   ) -> Registry:
    reg = get_fresh_registry(path=path,
                             security=security,
                             config=config,
                             local_name=local_name,
                             remote_name=remote_name)
    reg.initialize_as_admin()
    return reg
