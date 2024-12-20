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
        self.entry.bind('<Enter>', lambda event: self.show_tooltip())
        self.entry.bind('<Leave>', lambda event: self.remove_tooltip())

        self.tipwindow = None


    def show_tooltip(self):
        "Display text in tooltip window"
        # text = 'Lorem ipsum'
        text = self.setting.value

        if self.tipwindow is not None:
            return

        x, y, cx, cy = self.entry.bbox("insert")
        x = x + self.entry.winfo_rootx() + 57
        y = y + cy + self.entry.winfo_rooty() +27
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        self.tipwindow = tkinter.Toplevel(self.entry)
        self.tipwindow.wm_overrideredirect(1)
        self.tipwindow.wm_geometry("+%d+%d" % (x, y))
        label = tkinter.Label(
            self.tipwindow, text=text, justify='left',
            background="#ffffe0", relief='solid', borderwidth=1,
            font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def remove_tooltip(self):
        self.tipwindow.destroy()
        self.tipwindow = None