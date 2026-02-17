# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
''' options module with Options object
'''
from appxf import Stateful
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
    # new object with other content
    obj = PredefinedAttributes(state_int=42, state_str='new', state_list=['new'])
    # restore content
    obj.set_state(state)
    assert obj.state_list == ['test']
    assert obj.state_int == 42

# A derived class may update the attributes
@dataclass
class PredefinedAttributesDerived(PredefinedAttributes):
    state_new_int: int = 0
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
    # new object with other content
    obj = PredefinedAttributesDerived(state_int=42, state_str='new', state_list=['new'], state_new_int=15)
    # restore content
    obj.set_state(state)
    assert obj.state_list == ['test']
    assert obj.state_int == 42
    assert obj.state_new_int == 0


###############
## details
#/

# manual override of attribute and attribute_mask
def test_manual_get_state():
    obj = PredefinedAttributes(state_int=42, state_str='predefined', state_list=['predefined'])
    state = obj.get_state(attributes=['state_int', 'state_str', 'state_list'],
                          attribute_mask=['state_str'])
    assert 'state_int' in state
    assert 'state_list' in state
    assert len(state) == 2
    assert state['state_int'] == 42
    assert state['state_list'] == ['predefined']

###############
## error cases
#/

# state not being a dict
def test_state_no_dict():
    obj = PredefinedAttributes()
    state = ''
    with pytest.raises(TypeError) as exc:
        obj.set_state(state)
    assert 'uses a dict[str, StateType]' in str(exc.value)
    assert 'you provided: str' in str(exc.value)

# state including a non-string key
def test_state_wrong_key_type():
    obj = PredefinedAttributes()
    state = {b'state_int': 42}
    with pytest.raises(TypeError) as exc:
        obj.set_state(state)
    assert 'uses a dict[str, StateType]' in str(exc.value)
    assert "you provided a key: b'state_int'" in str(exc.value)
    assert 'of type bytes' in str(exc.value)

def test_state_wrong_key_value():
    obj = PredefinedAttributes()
    state = {'state_int': PredefinedAttributes()}
    with pytest.raises(TypeError) as exc:
        obj.set_state(state)
    assert 'uses a dict[str, StateType]' in str(exc.value)
    assert 'you provided a value for key=state_int of type PredefinedAttributes' in str(exc.value)

def test_state_import_wrong_key():
    obj = PredefinedAttributes()
    state = {'unsupported_key': 0}
    with pytest.raises(Warning) as exc:
        obj.set_state(state)
    assert 'PredefinedAttributes' in str(exc.value)
    assert 'includes attribute unsupported_key which is not expected' in str(exc.value)
    assert "expected are ['state_list']" in str(exc.value)

def test_state_export_wrong_key():
    class WrongExport(PredefinedAttributes):
        attributes = ['unsupported_key']
    obj = WrongExport()
    with pytest.raises(TypeError) as exc:
        obj.get_state()
    assert 'WrongExport' in str(exc.value)
