''' provide common functions for storage handling '''
import pytest
# (C) 2024 github/alexander-rd. Part of APPXF package. MIT license, see LICENSE
# file for details.

# No common stuff yet, but context will be a dictionary.

@pytest.fixture
def env_base():
    return {
        'path_testing': './.testing'
    }
