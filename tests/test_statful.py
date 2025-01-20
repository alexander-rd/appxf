''' options module with Options object
'''
from kiss_cf import Stateful
from dataclasses import dataclass, field

import pytest


###########################################
## Use Case: class with predefined symbols
@dataclass
class PredefinedAttributes(Stateful):
    state_int: int = 0
    state_str: str = 'test'
    state_list: list[str] = field(default_factory=lambda: ['test'])
    attributes = ['state_list']

# With only the list being defined, get_state() should only return this list
# and only restore this list:
def test_predefined_default():
    obj = PredefinedAttributes()
    state = obj.get_state()
    assert 'state_list' in state
    assert len(state) == 1
    assert state['state_list'] == ['test']
    # change content
    obj.state_int = 42
    obj.state_list = ['bla']
    # restore content
    obj.set_state(state)
    assert obj.state_list == ['test']
    assert obj.state_int == 42

# A derived class may update the attributes
@dataclass
class PredefinedAttributesDerived(PredefinedAttributes):
    state_new_int = 0
    # best way to extend is to add to the parent attributes setting:
    attributes = PredefinedAttributes.attributes + ['state_new_int']

# this test case is copied from test_predefined_default with state_new_int added
def test_predefined_derived():
    obj = PredefinedAttributesDerived()
    state = obj.get_state()
    print(obj.attributes)
    print(state)
    assert 'state_list' in state
    assert 'state_new_int' in state
    assert len(state) == 2
    assert state['state_list'] == ['test']
    assert state['state_new_int'] == 0
    # change content
    obj.state_int = 42
    obj.state_list = ['bla']
    obj.state_new_int = 42
    # restore content
    obj.set_state(state)
    assert obj.state_list == ['test']
    assert obj.state_int == 42
    assert obj.state_new_int == 0