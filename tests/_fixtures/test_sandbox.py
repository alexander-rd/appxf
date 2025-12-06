''' Test sandbox path handling

The test sandbox is a directory where each test case can create a sanbox for
files and folders needed during test case execution. This module provides
corresponding variables and helpers.
'''

import pytest
import os
import shutil
import toml

### Reading configuration from pyproject.toml
toml_data = toml.load(open('pyproject.toml'))
# get current project version:
project_version = toml_data['project']['version']
# get sandbox root directory for testing:
test_sandbox_root = toml_data['tool']['appxf']['test-sandbox-root']
print(f'Configuration from pyproject.toml:\n'
      f'Testing sandbox root: {test_sandbox_root}\n'
      f'Project version: {project_version}')

def init_test_sandbox_from_fixture(
    request: pytest.FixtureRequest,
    cleanup: bool = True) -> str:
    ''' Initialize a test sandbox from a pytest fixture (request)

    attributes:
        request -- the pytest fixture request object
        cleanup -- sandbox will be cleaned up (from previous tests),
                   default: True
    return: path to the created test sandbox
    '''
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
    path = test_sandbox_root
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
