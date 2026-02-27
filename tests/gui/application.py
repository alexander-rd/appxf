# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
'''
Resizing: First main frame has a border and is the only thing that must resize.
Switch Button: It toggle buttons to switch to start/second.
Switching must NOT resize the window.
'''

import tkinter

from appxf.gui.application import AppxfApplication
from appxf_matema.case_runner import ManualCaseRunner

app = AppxfApplication()
app.title('AppxfApplication Dummy')


class DummyFrame(tkinter.Frame):
    def __init__(self, *args, **kwargs):
        next_frame = kwargs.get('next_frame', 'start')
        kwargs.pop('next_frame')
        super().__init__(
            *args, **kwargs, highlightbackground='red', highlightthickness=2
        )

        button = tkinter.Button(
            self,
            text=f'Switch to [{next_frame}]',
            command=lambda: app.show_frame(next_frame),
        )
        button.pack(padx=150, pady=50)


# TODO: this interface is irritating/complex. Usually, I would just construct
# the frame and and put it into the application. From this POV here, it is not
# clear why I should provide the __init__ arugments in such a complicated
# fashion.
app.register_frame('start', DummyFrame, (), next_frame='second')
app.register_frame('second', DummyFrame, (), next_frame='start')
app.show_frame('start')

ManualCaseRunner().run()
