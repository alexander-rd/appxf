import tkinter
from tkinter import ttk

from appxf import logging
from kiss_cf.setting import AppxfSetting, AppxfSettingSelect
from .setting_gui import GridFrame, SettingFrame


class SettingSelectDropdown(GridFrame):
    ''' Dropdown with options according to AppxfSettingSelect

    Provides Events:
      <<ValueUpdated>> on any valid value update.
    '''
    log = logging.getLogger(__name__ + '.SettingSelectDropdown')

    def __init__(self, parent,
                 setting: AppxfSettingSelect,
                 **kwargs):
        '''Frame holding a single property.'''
        super().__init__(parent, **kwargs)
        self.setting = setting

        self.columnconfigure(1, weight=1)

        self.label = tkinter.Label(self, justify='right')
        self.label.config(text=setting.name + ':')
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky='NE')

        value = str(self.setting.input)
        self.sv = tkinter.StringVar(self, value)
        self.sv.trace_add(
            'write', lambda var, index, mode: self.value_update())

        self.entry_width = setting.gui_options.get('width', 15)
        self._place_combobox()

        self.tipwindow = None

    def _place_combobox(self):
        self.entry = ttk.Combobox(self, textvariable=self.sv, width=self.entry_width)
        key_list = list(self.setting.get_options()['select_map'].keys())
        key_list.sort()
        self.entry['values'] = key_list
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky='NEW')
        self.entry.bind('<Enter>', lambda event: self.show_tooltip())
        self.entry.bind('<Leave>', lambda event: self.remove_tooltip())

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
            print('ValueUpdated')
            self.event_generate('<<ValueUpdated>>')
        else:
            self.entry.config(foreground='red')

    def update(self):
        # an update implies that anything on the input SettingSelect changed.
        # Easiest way to handle this is by destroying the ComboBox and
        # re-creating it:
        self.entry.destroy()
        self._place_combobox()

    def show_tooltip(self):
        "Display text in tooltip window"
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
        if self.tipwindow is not None:
            self.tipwindow.destroy()
            self.tipwindow = None

class SettingSelectEditRowOne(GridFrame):
    '''

    Provides Events:
      <<DeleteOption>> on press of the "Delete" button
      <<ValueUpdated>> as forwarded event from the DropDown field
    '''

    def __init__(self, parent,
                 setting: AppxfSettingSelect):
        super().__init__(parent)
        self.setting = setting

        self._place_dropdown()
        self.delete_button = tkinter.Button(
            self, text='Delete',
            command=lambda: self.handle_delete_button())
        self.delete_button.grid(row=0, column=1, padx=5, pady=5, sticky='E')

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def _place_dropdown(self):
        self.dropdown = SettingSelectDropdown(self, setting=self.setting)
        self.dropdown.grid(row=0, column=0, sticky='EW')
        self.dropdown.bind('<<ValueUpdated>>',
                           lambda event: self.event_generate('<<ValueUpdated>>'))

    def update(self):
        self.dropdown.destroy()
        self._place_dropdown()

    def handle_delete_button(self):
        if self.setting.input in self.setting.options:
            del self.setting.options[self.setting.input]
        self.event_generate('<<DeleteOption>>')

class SettingSelectEditRowThree(GridFrame):
    '''

    Provides Events:
      <<SaveOption>> on press of the "Save" button
    '''
    def __init__(self, parent,
                 setting: AppxfSetting):
        super().__init__(parent)
        self.setting = setting
        self._place_entry()
        self.save_button = tkinter.Button(
            self, text='Save',
            command=lambda: self.handle_save_button())
        self.save_button.grid(row=0, column=1, padx=5, pady=5, sticky='E')

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def _place_entry(self):
        self.entry = SettingFrame(parent=self, setting=self.setting)
        self.entry.grid(row=0, column=0, sticky='EW')

    def update(self):
        if self.entry is not None:
            self.entry.destroy()
            self.entry = None
        self._place_entry()

    def handle_save_button(self):
        self.event_generate('<<SaveOption>>')

class SettingSelectEditFrame(GridFrame):
    ''' Frame to edit a SettingSelect

    Setting frames cannot store changes. You have to access this frame via a
    SettingDictFrame or handle the SettingDict in the GUI element you are
    creating.

    The Frame consists of three rows:
      1) The SettingSelect dropdown with delete button
      2) An entry field to for new/changed dropdown items
      3) A setting name entry and save button

    When selecting an option in the dropdown (1), the selection applies to (2)
    and (3). When using the delete button, the selected option is removed. When
    using the save button, the current value is added to the name in the
    setting.
    '''
    def __init__(self, parent,
                 setting: AppxfSettingSelect,
                 **kwargs):
        super().__init__(parent, **kwargs)
        # Date is maintained in the setting (SettingSelect) and a setting used
        # in the free entry field.
        self.parent = parent
        self.setting = setting
        self.value_setting: AppxfSetting = setting.base_setting_class(
            value=setting.value,
            name='select entry',
            **(setting.base_setting_kwargs))
        self.new_option_name_setting = AppxfSetting.new(str, value=setting.input, name='new option')
        # All three rows may be updated according to events such that the init
        # will be reused in actions. They fill the following fields:
        self.dropdown_row_frame = SettingSelectEditRowOne(self, setting=self.setting)
        self.dropdown_row_frame.grid(row=0, column=0, sticky='NEW')

        self.entry_row_frame = SettingFrame(self,
                                            setting=self.value_setting)
        self.entry_row_frame.grid(row=1, column=0, sticky='NSEW')

        self.save_row_frame = SettingSelectEditRowThree(self, setting=self.new_option_name_setting)
        self.save_row_frame.grid(row=2, column=0, sticky='SEW')

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)
        self.columnconfigure(0, weight=1)

        self.dropdown_row_frame.bind(
            '<<ValueUpdated>>',
            lambda event: self.handle_dropdown_update())
        self.dropdown_row_frame.bind('<<DeleteOption>>',
                                     lambda event: self.delete_option())
        self.save_row_frame.bind('<<SaveOption>>',
                                 lambda event: self.save_option())

    def handle_dropdown_update(self):
        print('handle_dropdown_update')
        self.new_option_name_setting.value = self.setting.input
        self.value_setting.value = self.setting.value
        self.entry_row_frame.update()
        self.save_row_frame.update()

    def save_option(self):
        # store new option
        self.setting.select_map[self.new_option_name_setting.value] = self.value_setting.value
        # select the new option
        self.setting.value = self.new_option_name_setting.value
        # Note: neither the entry field for new values nor the entry field for
        # the new option name need an update.
        self.dropdown_row_frame.update()

    def delete_option(self):
        # Delete current selection from the options
        if self.setting.input in self.setting.select_map:
            self.setting.select_map.pop(self.setting.input)
        # Default select the first item:
        if self.setting.select_map.keys():
            self.setting.value = list(self.setting.select_map.keys())[0]
        else:
            self.setting.value = ''
        # Apply SettingSelect state to the other two variables
        self.value_setting.value = self.setting.value
        self.new_option_name_setting.value = self.setting.input
        # Update all frames
        self.dropdown_row_frame.update()
        self.entry_row_frame.update()
        self.save_row_frame.update()

# The updated content in Save/Delete is not really updated content. It's more
# like "action triggered". The Action registration may need a more detailed
# concept on "actions".

class SettingSelectEditWindow(tkinter.Toplevel):
    def __init__(self, parent, setting: AppxfSettingSelect, **kwargs):
        super().__init__(parent, **kwargs)
        self.title(f'Editing {setting.name}')

        self.frame = SettingSelectEditFrame(self, setting=setting)
        self.frame.grid(row=0, column=0, sticky='NSEW')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

class SettingSelectFrame(SettingSelectDropdown):
    log = logging.getLogger(__name__ + '.SettingSelectFrame')

    def __init__(self, parent,
                 setting: AppxfSettingSelect,
                 **kwargs):
        '''Frame holding a single property.'''
        super().__init__(parent, setting=setting, **kwargs)
        self.setting = setting

        # add edit button if options are mutable
        if setting.options.get('mutable', False):
            self.edit_button = tkinter.Button(
                self, text='Edit',
                padx=0, pady=0, relief='flat',
                command=self.handle_edit_button
                )
            self.edit_button.grid(row=0, column=2, padx=5, pady=3, sticky='NW')

    def handle_edit_button(self):
        popup = SettingSelectEditWindow(self, setting=self.setting)
        popup.grab_set()
        self.wait_window(popup)
        # replace the dropdown to consider updated information
        self.update()