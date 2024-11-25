# This is how instances of a base class should be tested.

import pytest
from module import SubclassA, SubclassB

### Those two fixtures belong into the scope of SubclassA and SubclassB:
@pytest.fixture
def subclass_a_instance():
    # Initialize and return an instance of SubclassA with specific initialization
    return SubclassA(initialization_param='some_value_for_subclass_a')

@pytest.fixture
def subclass_b_instance():
    # Initialize and return an instance of SubclassB with specific initialization
    return SubclassB(initialization_param='some_value_for_subclass_b')

### This parametrizes a fixture for this test:
# * subclass may provide multiple initializers, predefined in a list of
#   fixtures to be merged here. List name may be
#   [test_storage_local.base_fixture_list].
@pytest.fixture(params=[pytest.lazy_fixture('subclass_a_instance'), pytest.lazy_fixture('subclass_b_instance')])
def subclass_instance(request):
    return request.param

### Now, test cases look like this:
def test_method_1(subclass_instance):
    assert subclass_instance.some_method_1() == expected_result_1

def test_method_2(subclass_instance):
    assert subclass_instance.some_method_2() == expected_result_2


### Test strategy when extending base classes:
# 1) Initialize own test suite to place the fixture and cover expectations after construction
# 2) Add new class to unit testing of all base classes (to cover base behavior)
#   * base class testing will inclue the the specific test files (inversion of
#     dependencies in testing: while subclass depends on base class in
#     implementation, the testing of the base class depends on the testing of the subclass)
# 3) Extend new class testing for specific behavior
#
# Base class tests will always test the defined object? Making no further
# assumptions on additional objects (hidden in fixture initialization)?
#
# Whether the subclass fixtures are true unit tests or not will depend on how
# they implement the fixtures to construct their objects.
#
# Candidates for this strategy:
#  * FileStorage, Storage, Storable
