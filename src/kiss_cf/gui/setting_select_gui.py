import tkinter
from PIL import Image, ImageTk
from tkinter import ttk
from pytablericons import FilledIcon, TablerIcons, OutlineIcon

from kiss_cf.setting import AppxfSetting, AppxfStringSelect
from .setting_gui import SettingFrame

class SettingSelectFrame(SettingFrame):
    def __init__(self, parent,
                 setting: AppxfStringSelect,
                 **kwargs):
        super().__init__(parent,
                         setting=setting,
                         **kwargs)

        # The StringVar in self.sv remains the same, there is no change
        # necessary. we just need to replyce the Entry by an OptionMenu
        self.entry.destroy()
        self.entry = ttk.Combobox(self, textvariable=self.sv)
        self.entry['values'] = list(setting._options.keys())
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky='NEW')

        # add edit button
        self.edit_button = tkinter.Button(self, text='Edit',
                                          padx=0, pady=0, relief='flat')
        self.edit_button.grid(row=0, column=2, padx=5, pady=5, sticky='NE')


