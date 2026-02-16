# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: Apache-2.0
''' provide common functions for storage handling '''
import pytest
import os.path
import shutil

from tests.fixtures.env_base import env_base

# TODO: fixture to be reconsidered after application context's were introduced.

@pytest.fixture
def env_test_directory(env_base, request):
    test_name = request.node.name
    # Provide basic test location:
    env_base['dir'] = os.path.join('./.testing', test_name)
    if os.path.exists(env_base['dir']):
        shutil.rmtree(env_base['dir'])
    os.makedirs(env_base['dir'], exist_ok=True)
    print(f'Setup: Cleaned path {env_base["dir"]}')
    return env_base
