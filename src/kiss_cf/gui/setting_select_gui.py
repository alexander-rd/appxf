import tkinter
from tkinter import ttk

from appxf import logging
from kiss_cf.setting import AppxfSetting, AppxfSettingSelect
from .setting_gui import GridFrame

class SettingSelectFrame(GridFrame):

    log = logging.getLogger(__name__ + '.SettingSelectFrame')

    def __init__(self, parent,
                 setting: AppxfSettingSelect,
                 **kwargs):
        '''Frame holding a single property.'''
        super().__init__(parent, **kwargs)

        self.columnconfigure(1, weight=1)

        self.setting = setting

        self.label = tkinter.Label(self, justify='right')
        self.label.config(text=setting.name + ':')
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky='NE')

        value = str(self.setting.value)
        self.sv = tkinter.StringVar(self, value)
        self.sv.trace_add(
            'write', lambda var, index, mode: self.value_update())

        entry_width = setting.gui_options.get('width', 15)
        self.entry = ttk.Combobox(self, textvariable=self.sv, width=entry_width)
        self.entry['values'] = list(setting.get_options()['select_map'].keys())
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky='NEW')
        self.entry.bind('<Enter>', lambda event: self.show_tooltip())
        self.entry.bind('<Leave>', lambda event: self.remove_tooltip())

        # add edit button if options are mutable
        if getattr(setting.options, 'mutable', False):
            self.edit_button = tkinter.Button(self, text='Edit',
                                            padx=0, pady=0, relief='flat')
            self.edit_button.grid(row=0, column=2, padx=5, pady=5, sticky='NE')

        self.tipwindow = None

    def is_valid(self):
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

    def show_tooltip(self):
        "Display text in tooltip window"
        # text = 'Lorem ipsum'
        text = self.setting.value

        if self.tipwindow is not None:
            return

        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        self.tipwindow = tkinter.Toplevel(self.entry)
        self.tipwindow.wm_overrideredirect(1)
        self.tipwindow.wm_geometry("+%d+%d" % (x, y))
        #self.tipwindow.maxsize(int(1/3*self.winfo_screenwidth()),
        #                       int(1/2*self.winfo_screenheight()))
        label = tkinter.Label(
            self.tipwindow, text=text, justify='left',
            background="#ffffe0", relief='solid', borderwidth=1,
            wraplength=self.winfo_width(),
            font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def remove_tooltip(self):
        self.tipwindow.destroy()
        self.tipwindow = None