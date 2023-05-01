from tests import fake_tkinter
fake_tkinter.activate()

import pytest
import tkinter

# Used to test logging:
# from kiss_cf import logging as kiss_logging
# kiss_logging.activate_logging()

from kiss_cf.application import KissApplication

class DummyFrame(tkinter.Frame):
    def __init__(self, parent, argOne, argTwo, *args, **kwargs):
        super().__init__(parent)
        self.argOne = argOne
        self.argTwo = argTwo
        self.args = list()
        self.kwargs = dict()
        for arg in enumerate(args):
            self.args.append(arg)
        for key, value in kwargs.items():
            self.kwargs[key] = value


def test_register_frame_wrong_type():
    af = KissApplication()

    with pytest.raises(TypeError) as e_info:
        af.register_frame('name', str)
    print(e_info)

def test_show_frame_not_existing():
    af = KissApplication()
    with pytest.raises(KeyError) as e_info:
        af.show_frame('dummy')
    print(e_info)

def test_register_frame():
    af = KissApplication()

    af.register_frame('dummy', DummyFrame,
                      'one', 'two', 'three', 'four',
                      hello='world', something='else')

    # ensure constructed and check the dummy frame
    af.show_frame('dummy')
    assert af._main_frame.argOne == 'one'
    assert af._main_frame.argTwo == 'two'
    assert af._main_frame.args[0][1] == 'three'
    assert af._main_frame.args[1][1] == 'four'
    assert af._main_frame.kwargs['hello'] == 'world'
    assert af._main_frame.kwargs['something'] == 'else'

    with pytest.raises(ValueError) as e_info:
        af.register_frame('dummy', DummyFrame)
    print(e_info)



