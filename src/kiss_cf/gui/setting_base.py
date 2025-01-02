'''
Provide GUI classes for KissProperty objects.
'''

import tkinter

from appxf import logging
from kiss_cf.setting import AppxfSetting

from .common import GridFrame, GridSetting

# TODO: better option on when to validate input:
# https://www.plus2net.com/python/tkinter-validation.php

# TODO: Class naming is a mess

# TODO: GUI options handling does not seem to be very straight

# TODO: Documentation of options

# TODO: the above suggests: larger review and rework

# TODO: There is an abstract SettingFrame missing which could be configured as
#       default for a setting.


class SettingFrameDefault(GridFrame):
    '''Frame holding a single property.'''
    log = logging.getLogger(__name__ + '.PropertyWidget')

    def __init__(self, parent,
                 setting: AppxfSetting,
                 **kwargs):
        super().__init__(parent, **kwargs)

        self.columnconfigure(1, weight=1)

        self.setting = setting

        self.label = tkinter.Label(self, justify='right')
        self.label.config(text=setting.name + ':')
        self.place(self.label, row=0, column=0)

        value = str(self.setting.value)
        self.sv = tkinter.StringVar(self, value)
        self.sv.trace_add(
            'write', lambda var, index, mode: self.value_update())

        entry_width = setting.gui_options.get('width', 15)
        entry_height = setting.gui_options.get('height', 1)
        if entry_height > 1:
            self.entry = tkinter.Text(self, width=entry_width, height=entry_height)
            self.entry.insert('1.0', self.setting.value)
            self.entry.bind('<KeyRelease>', lambda event: self._text_field_changed())
            entry_sticky = 'NSEW'
            x_padding = (5,0)
            self.rowconfigure(0, weight=1)
        else:
            self.entry = tkinter.Entry(self, textvariable=self.sv, width=entry_width)
            entry_sticky = 'NEW'
            x_padding = 5
            self.rowconfigure(0, weight=0)
        self.place(self.entry, row=0, column=1,
                   setting=GridSetting(padx=x_padding, pady=5,
                                       sticky=entry_sticky))
        # TODO: to apply place() properly without the nonsense setting, the
        # scollable Text must be distinguished from a non-scollable text. The
        # scrollable Text would become it's own widget (a frame with both
        # contained and no padding applied)

        # add scrollbar for long texts
        scrollbar = setting.gui_options.get('scrollbar', bool(entry_height >= 3))
        if scrollbar and isinstance(self.entry, tkinter.Text):
            self.scrollbar = tkinter.Scrollbar(self, orient=tkinter.VERTICAL,
                                               command=self.entry.yview) # type: ignore (entry is Text)
            self.place(self.scrollbar, row=0, column=2,
                       setting=GridSetting(padx=(0,5), sticky='NSE'))
            self.entry.configure(yscrollcommand=self.scrollbar.set)

    def update(self):
        if isinstance(self.entry, tkinter.Text):
            self.entry.delete('1.0', tkinter.END)
            self.entry.insert('1.0', self.setting.value)
        else:
            self.sv.set(self.setting.value)
        super().update()

    def _text_field_changed(self):
        value = self.entry.get('1.0', tkinter.END)
        if value.endswith('\n'):
            value = value[0:-1]
        self.sv.set(value)

    def is_valid(self) -> bool:
        return self.setting.validate(self.sv.get())

    def focus_set(self):
        self.entry.focus_set()

    def value_update(self):
        value = self.sv.get()
        valid = self.setting.validate(value)
        if valid:
            self.setting.value = value
            self.entry.config(foreground='black')
        else:
            self.entry.config(foreground='red')


class SettingFrameBool(GridFrame):
    '''CheckBox frame for a single boolean.'''
    log = logging.getLogger(__name__ + '.BoolCheckBoxWidget')

    def __init__(self, parent,
                 setting: AppxfSetting,
                 kiss_options: dict = dict(),
                 **kwargs):
        super().__init__(parent, **kwargs)

        self.rowconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

        self.setting = setting

        self.label = tkinter.Label(self, justify='right')
        self.label.config(text=setting.name + ':')
        self.place(self.label, row=0, column=0)

        self.iv = tkinter.IntVar(self, value=self.setting.value)

        # TODO: have width from some input
        self.checkbox = tkinter.Checkbutton(self, text='', variable=self.iv)
        self.place(self.checkbox, row=0, column=1)

        self.iv.trace_add(
            'write', lambda var, index, mode: self.value_update())

    def is_valid(self):
        # Checkbox value will always be valid
        return True

    def focus_set(self):
        # there is nothing we can focus on
        pass

    def value_update(self):
        self.setting.value = self.iv.get()
