''' Helper functions to generate dummy APPXF objects for testing
'''

import os

from kiss_cf.storage import LocalStorage, RamStorage
from kiss_cf.security import Security, SecurityMock
from kiss_cf.registry import Registry
from kiss_cf.config import Config

def get_dummy_config() -> Config:
    return Config()

def get_dummy_user_config() -> Config:
    config = Config()
    config.add_section(section='USER')
    return config

def get_security_unlocked(path: str | None = None) -> Security:
    if path is None:
        # use security mock
        sec = SecurityMock()
    else:
        sec = Security(
            salt='test',
            file=os.path.join(path, 'user'))
    sec.init_user('password')
    sec.unlock_user('password')
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
