# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
''' provide common functions for storage handling '''
import pytest
# No common stuff yet, but context will be a dictionary.

@pytest.fixture
def env_base():
    return {
        'path_testing': './.testing'
    }
