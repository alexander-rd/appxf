# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: Apache-2.0
import pytest
import tkinter

from tests._fixtures import fake_tkinter
fake_tkinter.activate()

from appxf.gui.application import AppxfApplication # noqa E402

# TODO: This test case was rendered "manual" but the cases look like automated
# ones. Cannot reconsider right now since it needs more effort.

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
    af = AppxfApplication()

    with pytest.raises(TypeError) as e_info:
        af.register_frame('name', str)
    print(e_info)


def test_show_frame_not_existing():
    af = AppxfApplication()
    with pytest.raises(KeyError) as e_info:
        af.show_frame('dummy')
    print(e_info)


def test_register_frame():
    af = AppxfApplication()

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
