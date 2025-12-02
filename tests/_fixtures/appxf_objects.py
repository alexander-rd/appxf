import os
import pytest
import shutil

from kiss_cf.storage import LocalStorage, RamStorage, JsonSerializer
from kiss_cf.security import Security, SecurityMock
from kiss_cf.registry import Registry
from kiss_cf.config import Config

testing_base_dir = './.testing'

def get_initialized_test_path(
    request: pytest.FixtureRequest,
    cleanup: bool = True):
    # This is the current test function/method name:
    test_name = request.node.name

    # Obtain the module name:
    module = request.node.module
    module_name = module.__name__

    # Obtain folder of the current module. Assuming a structure like
    # ./tests/module_name/test_file.py, the module_name should be part of the
    # created subdirectory for test files.
    module_path = request.node.fspath
    module_directory = os.path.dirname(str(module_path))
    module_last_folder = os.path.basename(module_directory)
    if module_last_folder in ['test', 'tests']:
        module_last_folder = ''

    # Also obtain the class name in case the executed function is actually a
    # method. In such a case, the test class should also be part of the created
    # testing subdirectory.
    test_cls = request.node.cls
    class_name = ''
    if test_cls:
        class_name = test_cls.__name__

    # This would now be the directory to be created
    path = testing_base_dir
    if module_last_folder and class_name:
        path = os.path.join(path, f'{module_last_folder}.{module_name}.{class_name}')
    elif module_last_folder:
        path = os.path.join(path, f'{module_last_folder}.{module_name}')
    elif class_name:
        path = os.path.join(path, f'{module_name}.{class_name}')
    else:
        path = os.path.join(path, f'{module_name}')
    path = os.path.join(path, test_name)

    # Cleanup directors:
    if cleanup and os.path.exists(path):
        shutil.rmtree(path)
    # and ensure it will be existing:
    os.makedirs(path, exist_ok=True)
    print(f'Created and cleanup testing path: {path}')
    return path

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
        sec = Security(salt='test',
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
