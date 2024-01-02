''' provide common functions for storage handling '''

import pytest
import os.path
import shutil

from tests.fixtures.env_base import env_base

@pytest.fixture
def env_test_directory(env_base, request):
    test_name = request.node.name
    # Provide basic test location:
    env_base['dir'] = os.path.join('./.testing', test_name)
    if os.path.exists(env_base['dir']):
        shutil.rmtree(env_base['dir'])
    os.mkdir(env_base['dir'])
    print(f'Setup: Cleaned path {env_base["dir"]}')
    return env_base
