# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
''' Helper functions to generate dummy APPXF objects for testing
'''

import os

from appxf.storage import LocalStorage, RamStorage, Storage
from appxf.security import Security
from appxf.registry import Registry
from appxf.config import Config

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
def get_security(path: str | bytes | None = None) -> Security:
    if path is None:
        storage = RamStorage()
    elif isinstance(path, bytes):
        storage = RamStorage(ram_area=str(path))
    else:
        storage = path
    sec = Security(
        salt='test',
        storage=storage)
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

def perform_registration(
        registry: Registry,
        admin_registry: Registry,
        storage_scope: str = 'user',
        admin_storage_scope: str = 'admin',
        roles: list[str] | None = None):
    if roles is None:
        roles = ['user']

    # Ensure admin keys are available:
    Storage.switch_context(admin_storage_scope)
    admin_key_bytes = admin_registry.get_admin_key_bytes()
    Storage.switch_context(storage_scope)
    registry.set_admin_key_bytes(admin_key_bytes)
    # Get request and register:
    request_bytes = registry.get_request_bytes()
    Storage.switch_context(admin_storage_scope)
    request = admin_registry.get_request_data(request_bytes)
    new_user_id = admin_registry.add_user_from_request(request=request, roles=roles)
    print(f'{admin_storage_scope} (user ID {admin_registry.user_id}) registered '
          f'{storage_scope} with USER ID {new_user_id} and roles {roles}')
    response_bytes = admin_registry.get_response_bytes(new_user_id)
    # Apply response to fresh registry
    Storage.switch_context(storage_scope)
    registry.set_response_bytes(response_bytes)
    Storage.switch_context('')
