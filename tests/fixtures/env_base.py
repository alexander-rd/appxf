''' provide common functions for storage handling '''
import pytest

# No common stuff yet, but context will be a dictionary.

@pytest.fixture
def env_base():
    return {
        'path_testing': './.testing'
    }
