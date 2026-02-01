'''
Provide GUI classes for APPXF Setting objects.
'''
from abc import ABC, abstractmethod
import tkinter

from appxf import logging
from appxf.setting import Setting, SettingBool

from .common import GridFrame, GridSetting

# TODO: better option on when to validate input:
# https://www.plus2net.com/python/tkinter-validation.php


class SettingFrameBase(GridFrame, ABC):
    ''' defining required interfaces for setting based frames '''
    def __init__(self,
                 parent: tkinter.BaseWidget,
                 read_only: bool = False,
                 **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.read_only = read_only

    @abstractmethod
    def is_valid(self) -> bool:
        ''' Maintained setting state is valid '''


class SettingFrameDefault(SettingFrameBase):
    '''Frame holding a single property.'''
    supports = [Setting]
    log = logging.getLogger(__name__ + '.PropertyWidget')

    def __init__(self, parent,
                 setting: Setting,
                 **kwargs):
        super().__init__(parent, **kwargs)

        self.columnconfigure(1, weight=1)

        self.setting = setting

        # Place label - still place something empty if label is '' to satisfy
        # implementations expecting something (like alignment of columns)
        self.label = tkinter.Label(self, justify='right')
        if setting.options.name:
            self.label.config(text=setting.options.name + ':')
        else:
            self.label.config(text='')
        self.place(self.label, row=0, column=0)

        # The following line was str(self.setting.value) before but the string
        # conversion must be handled by the setting class for stranger examples
        # like SettingBase64
        value = self.setting.to_string()
        self.sv = tkinter.StringVar(self, value)
        self.sv.trace_add(
            'write', lambda var, index, mode: self.value_update())

        entry_width = getattr(setting.options, 'display_width', 15)
        entry_height = getattr(setting.options, 'display_height', 1)
        if entry_height > 1:
            self.entry = tkinter.Text(
                self, width=entry_width, height=entry_height)
            self.entry.insert('1.0', self.setting.value)
            self.entry.bind(
                '<KeyRelease>', lambda event: self._text_field_changed())
            entry_sticky = 'NSEW'
            x_padding = (5, 0)
            self.rowconfigure(0, weight=1)
        else:
            self.entry = tkinter.Entry(
                self, textvariable=self.sv, width=entry_width)
            entry_sticky = 'NEW'
            x_padding = 5
            self.rowconfigure(0, weight=0)
        self._handle_read_only()

        self.place(self.entry, row=0, column=1,
                   setting=GridSetting(padx=x_padding, pady=5,
                                       sticky=entry_sticky))
        # TODO #22: to apply place() properly without the nonsense setting, the
        # scollable Text must be distinguished from a non-scollable text. The
        # scrollable Text would become it's own widget (a frame with both
        # contained and no padding applied)

        # add scrollbar for long texts
        scrollbar = getattr(
            setting.options, 'scrollbar', bool(entry_height >= 3))
        if scrollbar and isinstance(self.entry, tkinter.Text):
            self.scrollbar = tkinter.Scrollbar(
                self, orient=tkinter.VERTICAL,
                command=self.entry.yview)  # type: ignore (entry is Text)
            self.place(self.scrollbar, row=0, column=2,
                       setting=GridSetting(padx=(0, 5), sticky='NSE'))
            self.entry.configure(yscrollcommand=self.scrollbar.set)

    def _handle_read_only(self, deactivate: bool = False):
        if self.read_only:
            if deactivate:
                self.entry.config(state='normal')
            else:
                if isinstance(self.entry, tkinter.Text):
                    self.entry.config(state='disabled')
                else:
                    self.entry.config(state='readonly')

    def update(self):
        self._handle_read_only(deactivate=True)
        if isinstance(self.entry, tkinter.Text):
            self.entry.delete('1.0', tkinter.END)
            self.entry.insert('1.0', self.setting.value)
        else:
            self.sv.set(self.setting.value)
        self._handle_read_only()
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


class SettingFrameBool(SettingFrameBase):
    '''CheckBox frame for a single boolean.'''
    supports = [SettingBool]
    log = logging.getLogger(__name__ + '.BoolCheckBoxWidget')

    def __init__(self, parent,
                 setting: Setting,
                 **kwargs):
        super().__init__(parent, **kwargs)

        self.rowconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

        self.setting = setting

        self.label = tkinter.Label(self, justify='right')
        self.label.config(text=setting.options.name + ':')
        self.place(self.label, row=0, column=0)

        self.iv = tkinter.IntVar(self, value=self.setting.value)

        self.checkbox = tkinter.Checkbutton(self, text='', variable=self.iv)
        self.place(self.checkbox, row=0, column=1)

        self.iv.trace_add(
            'write', lambda var, index, mode: self.value_update())

    def is_valid(self) -> bool:
        # Checkbox value will always be valid
        return True

    def focus_set(self):
        # there is nothing we can focus on
        pass

    def value_update(self):
        self.setting.value = self.iv.get()
