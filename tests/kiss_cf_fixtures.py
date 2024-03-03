import os.path
import pytest
import shutil

@pytest.fixture
def empty_test_location(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)
    yield path
    if os.path.exists(path):
        shutil.rmtree(path)