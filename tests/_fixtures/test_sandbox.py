# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
''' Test sandbox path handling

The test sandbox is a directory where each test case can create a sanbox for
files and folders needed during test case execution. This module provides
corresponding variables and helpers.
'''
import pytest
import os
import shutil
import toml
import inspect
from pathlib import Path

### Reading configuration from pyproject.toml
try:
    toml_data = toml.load(open('pyproject.toml'))
    # get current project version:
    project_version = toml_data['project']['version']
    # get sandbox root directory for testing:
    test_sandbox_root = toml_data['tool']['appxf']['test-sandbox-root']
    print(f'Configuration from pyproject.toml:\n'
      f'Testing sandbox root: {test_sandbox_root}\n'
      f'Project version: {project_version}')
except FileNotFoundError:
    print('Warning: no pyproject.toml was found.')
    project_version = ''
    test_sandbox_root = '.testing'


def init_test_sandbox_from_fixture(
    request: pytest.FixtureRequest,
    cleanup: bool = True) -> str:
    ''' Create a sandbox from a pytest fixture (request) returning the
    path as string

    attributes:
        request -- the pytest fixture request object cleanup -- sandbox will be
        cleaned up (from previous tests),
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

    # Also obtain the class name in case the executed function is actually a
    # method. In such a case, the test class should also be part of the created
    # testing subdirectory.
    test_cls = request.node.cls
    class_name = ''
    if test_cls:
        class_name = test_cls.__name__

    return _init_test_sandbox(module_name, module_directory, test_name, class_name, cleanup)

def init_test_sandbox_for_caller_module(cleanup: bool = True) -> str:
    '''Create a sandbox for the caller returning the path as string

    Arguments:
        cleanup -- sandbox will be cleaned up (from previous runs), default: True
    Return: path to the created test sandbox
    '''
    # Identify the calling frame and resolve module/path information for namespacing.
    caller = inspect.stack()[1]
    caller_path = Path(caller.filename).resolve()
    caller_module = inspect.getmodule(caller.frame)
    module_name = caller_module.__name__ if caller_module and caller_module.__name__ != '__main__' else ''
    print(f'Create sandbox caller module [{module_name}] in path [{caller_path}]')
    # Fall back to a path-derived module name when no module is available.
    if not module_name:
        module_name = caller_path.stem

    module_directory = caller_path.parent.as_posix()

    # Intended use of this sandbox creation is for manual test cases where the
    # file itself is the test case. Therefore, only the module name (test case
    # name) and the path to this module matter. Class name does not matter.
    return _init_test_sandbox(
        module_name='',
        module_directory=module_directory,
        test_name=module_name,
        class_name='',
        cleanup=cleanup)

def _init_test_sandbox(module_name: str,
                       module_directory: str,
                       test_name: str,
                       class_name: str = '',
                       cleanup: bool = True) -> str:
    print(f'Sandboxing for module [{module_name}] in [{module_directory}] '
          f'the test [{test_name}] '
          f'{f"(class: {class_name})" if class_name else "(no class)"}'
          f'{" with cleanup." if cleanup else "."}')
    sandbox_root_parent = Path(test_sandbox_root).resolve().parent
    module_path = Path(module_directory).resolve()
    try:
        relative_module_path = module_path.relative_to(sandbox_root_parent).as_posix()
    except ValueError:
        relative_module_path = module_path.name
    if relative_module_path in ['test', 'tests']:
        relative_module_path = ''

    path = test_sandbox_root
    if relative_module_path:
        path = os.path.join(path, relative_module_path)
    if module_name:
        path = os.path.join(path, module_name)
    if class_name:
        path = os.path.join(path, class_name)
    if test_name:
        path = os.path.join(path, test_name)

    if cleanup and os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)
    print(f'Sandbox path {path}')
    return path
