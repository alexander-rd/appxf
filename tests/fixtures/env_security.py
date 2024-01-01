import pytest
import os.path

from kiss_cf.security import Security

from tests.fixtures.env_base import env_base
from tests.fixtures.env_storage import env_test_directory

@pytest.fixture()
def env_security_unlocked(env_test_directory):
    env = env_test_directory
    sec = Security(salt='test',
                   file=os.path.join(env['dir'], 'user'))
    sec.init_user('password')
    sec.unlock_user('password')
    env['security'] = sec
    return env
