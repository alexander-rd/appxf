import tkinter
from tkinter import ttk

from appxf import logging
from kiss_cf.setting import AppxfSetting, AppxfSettingSelect
from .common import ButtonFrame, FrameWindow
from .setting_gui import GridFrame, SettingFrame, SettingDictWindow
from copy import deepcopy


class SettingSelectDropdown(GridFrame):
    ''' Dropdown with options according to AppxfSettingSelect

    Provides Events:
      <<ValueUpdated>> on any valid value update.
    '''
    log = logging.getLogger(__name__ + '.SettingSelectDropdown')

    def __init__(self, parent,
                 setting: AppxfSettingSelect,
                 tooltip: bool = True,
                 **kwargs):
        '''Frame holding a single property.'''
        super().__init__(parent, **kwargs)
        self.setting = setting
        self.tooltip = tooltip

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
        self.entry['values'] = self.setting.get_options()
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky='NEW')
        if self.tooltip:
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
            self.event_generate('<<ValueUpdated>>')
        else:
            self.entry.config(foreground='red')

    def update(self):
        # an update implies that anything on the input SettingSelect changed.
        # Easiest way to handle this is by destroying the ComboBox and
        # re-creating it:
        #self.entry.destroy()
        self.sv.set(self.setting.input)
        #self._place_combobox()
        self.entry['values'] = self.setting.get_options()
        super().update()

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

class _SettingSelectEditRowOne(GridFrame):
    ''' Holds GUI Elements WITHOUT actions

    Provides Events:
      <<Add>>, <<Delete>> -- corresponding buttons pressed
      <<ValueUpdated>> -- dropdown selection changed (forwarded from
          dropdown)
    '''
    def __init__(self, parent,
                 setting: AppxfSettingSelect):
        super().__init__(parent)
        self.setting = setting

        # column=0:
        self._place_dropdown()

        # column=1: button frame
        self.button_frame = ButtonFrame(self, buttons=['Delete', 'Add'])
        self.place(self.button_frame, row=0, column=1)
        self.button_frame.bind('<<Delete>>', lambda event: self.event_generate('<<Delete>>'))
        self.button_frame.bind('<<Add>>', lambda event: self.event_generate('<<Add>>'))

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def _place_dropdown(self):
        self.dropdown = SettingSelectDropdown(self, setting=self.setting)
        self.place(widget=self.dropdown, row=0, column=0)
        self.dropdown.bind('<<ValueUpdated>>',
                           lambda event: self.event_generate('<<ValueUpdated>>'))

    def update(self):
        self.dropdown.destroy()
        self._place_dropdown()
        super().update()

class SettingSelectEdit(GridFrame):
    ''' Frame to edit a SettingSelect

    Setting frames cannot store changes. You have to access this frame via a
    SettingDictFrame or handle the SettingDict in the GUI element you are
    creating.

    The Frame consists of three rows:
      1) The SettingSelect dropdown with delete/add button
      2) An entry field to for new/changed dropdown items
      3) A setting name entry and save button

    When selecting an option in the dropdown (1), the selection applies to (2)
    and (3). When using the delete button, the selected option is removed. When
    using the save button, the current value is added to the name in the
    setting.
    '''
    log = logging.getLogger(__name__ + '.SettingSelectEdit')

    def __init__(self, parent,
                 setting: AppxfSettingSelect,
                 **kwargs):
        super().__init__(parent, **kwargs)
        # Data is maintained in the setting (SettingSelect) and a setting used
        # in the free entry field.
        self.setting = setting
        self.value_setting: AppxfSetting = setting.base_setting_class(
            value=setting.value,
            name='select entry',
            **(setting.base_setting_kwargs))
        # All three rows may be updated according to events such that the init
        # will be reused in actions. They fill the following fields:
        self.dropdown_frame = _SettingSelectEditRowOne(self, setting=self.setting)
        self.dropdown_frame.place(self.dropdown_frame, row=0, column=0)

        self.setting_frame = SettingFrame(self,
                                          setting=self.value_setting)
        self.place(self.setting_frame, row=1, column=0)

        self.dropdown_frame.bind(
            '<<ValueUpdated>>',
            lambda event: self.handle_dropdown_update())
        self.dropdown_frame.bind('<<Delete>>',
                                 lambda event: self.handle_delete_option())
        self.dropdown_frame.bind('<<Add>>',
                                 lambda event: self.handle_add_option())

    def handle_dropdown_update(self):
        self.log.debug(f'Setting [{self.setting.name}] updated')
        self.value_setting.value = self.setting.value
        self.setting_frame.update()

    def handle_delete_option(self):
        self.log.debug(f'Deleting Option [{self.setting.input}] from setting [{self.setting.name}]')
        # Delete current selection from the options
        self.setting.delete_option(self.setting.input)
        # Apply SettingSelect state to the entry variable
        self.value_setting.value = self.setting.value
        # Update all frames
        self.dropdown_frame.update()
        self.setting_frame.update()

    def handle_add_option(self):
        if not self.setting_frame.is_valid():
            self.log.warning(f'Current value for setting [{self.setting.name}] is not valid')
            return

        new_option_setting = AppxfSetting.new(str, value=self.setting.input, name='Option Name')
        popup = SettingDictWindow(parent=self,
                                  setting=new_option_setting,
                                  title='Save setting as ...')
        popup.grab_set()
        self.wait_window(popup)
        if popup.last_event == '<<Cancel>>':
            return
        new_option = new_option_setting.value
        self.setting.add_option(option=new_option,
                                value=self.value_setting.input)
        self.setting.value = new_option
        # Update all frames
        self.log.debug(f'Added Option [{new_option}] for setting [{self.setting.name}]')
        self.dropdown_frame.update()
        self.setting_frame.update()

# The updated content in Save/Delete is not really updated content. It's more
# like "action triggered". The Action registration may need a more detailed
# concept on "actions".

class SettingSelectEditWindow(FrameWindow):
    log = logging.getLogger(__name__ + '.SettingSelectEditWindow')

    def __init__(self, parent, setting: AppxfSettingSelect, **kwargs):
        super().__init__(parent,
                         title=f'Editing {setting.name}',
                         buttons=['Cancel', 'OK'],
                         closing='Cancel',
                         **kwargs)
        self.setting = setting
        self.backup_options = deepcopy(self.setting.options)
        self.backup_setting = self.setting.input
        self.setting_frame = SettingSelectEdit(self, setting=setting)
        self.place_frame(self.setting_frame)

        self.bind('<<Cancel>>', lambda event: self.handle_cancel_button())
        self.bind('<<OK>>', lambda event: self.handle_ok_button())

    def handle_ok_button(self):
        self.log.debug('OK')
        self.destroy()

    def handle_cancel_button(self):
        self.log.debug('Cancel')
        self.setting.options = deepcopy(self.backup_options)
        self.setting.value = self.backup_setting
        self.destroy()

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
        super().update()
