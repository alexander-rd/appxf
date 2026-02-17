# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
import tkinter

from tkinter import ttk
from copy import deepcopy

from appxf import logging
from appxf.setting import Setting, SettingSelect

from . import GridFrame
from .common import ButtonFrame, GridToplevel
from .setting_base import SettingFrameBase, SettingFrameDefault


class _DropdownOnly(SettingFrameBase):
    ''' Dropdown with options according to AppxfSettingSelect

    Provides Events:
      <<ValueUpdated>> on any valid value update.
    '''
    log = logging.getLogger(__name__ + '.SettingSelectDropdown')

    def __init__(self, parent,
                 setting: SettingSelect,
                 tooltip: bool = True,
                 **kwargs):
        '''Frame holding a single property.'''
        super().__init__(parent, **kwargs)
        self.setting = setting
        self.tooltip = tooltip

        self.columnconfigure(1, weight=1)

        self.label = tkinter.Label(self, justify='right')
        self.label.config(text=setting.options.name + ':')
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky='NE')

        value = str(self.setting.input)
        self.sv = tkinter.StringVar(self, value)
        self.sv.trace_add(
            'write', lambda var, index, mode: self.value_update())

        self.entry_width = getattr(setting.options, 'display_width', 15)
        self._place_combobox()

        self.tipwindow = None

    def _place_combobox(self):
        self.entry = ttk.Combobox(
            self, textvariable=self.sv, width=self.entry_width)
        self.entry['values'] = self.setting.get_select_keys()
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky='NEW')
        if self.tooltip:
            self.entry.bind('<Enter>', lambda event: self.show_tooltip())
            self.entry.bind('<Leave>', lambda event: self.remove_tooltip())

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
        self.sv.set(self.setting.input)
        self.entry['values'] = self.setting.get_select_keys()
        super().update()

    def show_tooltip(self):
        "Display text in tooltip window"
        text = self.setting.value

        if self.tipwindow is not None:
            return

        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        self.tipwindow = tkinter.Toplevel(self.entry)
        self.tipwindow.wm_overrideredirect(True)
        self.tipwindow.wm_geometry("+%d+%d" % (x, y))
        # self.tipwindow.maxsize(int(1/3*self.winfo_screenwidth()),
        #                        int(1/2*self.winfo_screenheight()))
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

    def is_valid(self):
        return self.setting.validate(self.sv.get())


class _DropdownWithButtons(SettingFrameBase):
    ''' Holds GUI Elements WITHOUT actions

    Note that Save and Delete buttons are only placed dependent on mutable
    settings. Delete button requires mutable_items and save button requires
    either mutable_list (only new settings can be created) and/or mutable_items
    (existing settings can be changed). The default behavior of <<Save>> skips
    the entry for the new field item if mutable_list is False.

    Provides Events:
      <<Save>>, <<Delete>> -- corresponding buttons pressed
      <<ValueUpdated>> -- dropdown selection changed (forwarded from
          dropdown)
    '''
    def __init__(self, parent,
                 setting: SettingSelect):
        super().__init__(parent)
        self.setting = setting

        # column=0:
        self._place_dropdown()

        # column=1: button frame
        if setting.options.mutable_list:
            button_list = ['Delete', 'Save']
        elif setting.options.mutable_items:
            button_list = ['Save']
        else:
            button_list = ['']

        self.button_frame = ButtonFrame(self, buttons=button_list)
        self.place(self.button_frame, row=0, column=1)
        if 'Delete' in button_list:
            self.button_frame.bind(
                '<<Delete>>', lambda event: self.event_generate('<<Delete>>'))
        if 'Save' in button_list:
            self.button_frame.bind(
                '<<Save>>', lambda event: self.event_generate('<<Save>>'))

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def _place_dropdown(self):
        self.dropdown = _DropdownOnly(self, setting=self.setting)
        self.place(widget=self.dropdown, row=0, column=0)
        self.dropdown.bind(
            '<<ValueUpdated>>',
            lambda event: self.event_generate('<<ValueUpdated>>'))

    def update(self):
        self.dropdown.destroy()
        self._place_dropdown()
        super().update()

    def is_valid(self):
        return self.dropdown.is_valid()


class SettingSelectDetailFrame(SettingFrameBase):
    ''' Frame to edit a SettingSelect

    Setting frames cannot store changes. You have to access this frame via a
    SettingDictFrame or handle the SettingDict in the GUI element you are
    creating.

    The Frame consists of three elements:
      1) The SettingSelect dropdown (top left)
      2) delete/save button dependent on mutable_list and mutable_items
         settings (top right)
      2) An entry field for new/changed dropdown items which is editable
         dependent on mutable_value (bottom)

    When selecting an option in the dropdown (1), the selection applies to (2)
    and (3). When using the delete button, the selected option is removed. When
    using the save button, the current value is added to the name in the
    setting.
    '''
    log = logging.getLogger(__name__ + '.SettingSelectEdit')

    def __init__(self, parent,
                 setting: SettingSelect,
                 **kwargs):
        super().__init__(parent, **kwargs)
        # Data is maintained in the setting (SettingSelect) and a setting used
        # in the free entry field.
        self.setting = setting
        # All three rows may be updated according to events such that the init
        # will be reused in actions. They fill the following fields:
        self.dropdown_frame = _DropdownWithButtons(self, setting=self.setting)
        self.dropdown_frame.place(self.dropdown_frame, row=0, column=0)

        self.setting_frame = GridFrame.get_frame(
            self,
            setting.base_setting,
            read_only=(not setting.options.custom_value))
        self.place(self.setting_frame, row=1, column=0)

        self.dropdown_frame.bind(
            '<<ValueUpdated>>',
            lambda event: self._handle_dropdown_update())
        self.dropdown_frame.bind('<<Delete>>',
                                 lambda event: self._handle_delete_option())
        self.dropdown_frame.bind('<<Save>>',
                                 lambda event: self._handle_save_option())

    def _handle_dropdown_update(self):
        # TODO: value should not be printed here if it's a password.
        self.log.debug(f'Setting [{self.setting.options.name}] updated: {self.setting.base_setting.value}')
        self.setting_frame.update()

    def _handle_delete_option(self):
        self.log.debug(
            f'Deleting Option [{self.setting.input}] '
            f'from setting [{self.setting.options.name}]')
        # Delete current selection from the options
        self.setting.delete_select_key(self.setting.input)
        # Apply SettingSelect state to the entry variable
        self.setting.base_setting.value = self.setting.value
        # Update all frames
        self.dropdown_frame.update()
        self.setting_frame.update()

    def _handle_save_option(self):
        if not self.setting_frame.is_valid():
            self.log.warning(
                f'Current value for setting [{self.setting.options.name}] '
                f'is not valid')
            return

        if self.setting.options.mutable_list:
            # adding new items is allowed and the user needs to enter this new
            # item name (but may keep the current one)
            new_option_setting = Setting.new(str,
                                             value=self.setting.input,
                                             name='Option Name')
            popup = GridToplevel(
                parent=self,
                title='Save setting as ...',
                closing=['Cancel', 'OK'])
            popup_frame = SettingFrameDefault(
                parent=popup,
                setting=new_option_setting)
            popup.place_frame(popup_frame)
            popup.grab_set()
            self.wait_window(popup)
            if popup.last_event == '<<Cancel>>':
                return
            new_option = new_option_setting.value
        else:
            # only changing current value content is allowed and the "new"
            # option name is the current option name:
            new_option = self.setting.input

        self.setting.add_select_item(
            option=new_option,
            value=self.setting.base_setting.input)
        self.setting.value = new_option
        # Update all frames
        self.log.debug(
            f'Added Option [{new_option}] for '
            f'setting [{self.setting.options.name}]')
        self.dropdown_frame.update()
        self.setting_frame.update()

    def is_valid(self) -> bool:
        return self.setting_frame.is_valid()

# The updated content in Save/Delete is not really updated content. It's more
# like "action triggered". The Action registration may need a more detailed
# concept on "actions".


class SettingSelectWindow(GridToplevel):
    log = logging.getLogger(__name__ + '.SettingSelectEditWindow')

    def __init__(self, parent, setting: SettingSelect, **kwargs):
        super().__init__(parent,
                         title=f'Editing {setting.options.name}',
                         buttons=['Cancel', 'OK'],
                         closing='Cancel',
                         **kwargs)
        self.setting = setting
        self.backup_options = deepcopy(self.setting.options)
        self.backup_setting = self.setting.input
        self.setting_frame = SettingSelectDetailFrame(self, setting=setting)
        self.place_frame(self.setting_frame)

        self.bind('<<Cancel>>', lambda event: self._handle_cancel_button())
        self.bind('<<OK>>', lambda event: self._handle_ok_button())

    def _handle_ok_button(self):
        self.log.debug('OK')
        self.destroy()

    def _handle_cancel_button(self):
        self.log.debug('Cancel')
        self.setting.options = deepcopy(self.backup_options)
        self.setting.value = self.backup_setting
        self.destroy()


class SettingSelectFrame(_DropdownOnly):
    supports = [SettingSelect]
    log = logging.getLogger(__name__ + '.SettingSelectFrame')

    def __init__(self, parent,
                 setting: SettingSelect,
                 **kwargs):
        '''Frame holding a single property.'''
        super().__init__(parent, setting=setting, **kwargs)
        self.setting = setting

        # TODO: there is behavior missing to support 'mutable_items'

        # add edit button if options are mutable
        if (getattr(setting.options, 'mutable_list', False)):
            self.edit_button = tkinter.Button(
                self, text='Edit',
                padx=0, pady=0, relief='flat',
                command=self._handle_edit_button
                )
            self.edit_button.grid(row=0, column=2, padx=5, pady=3, sticky='NW')

    def _handle_edit_button(self):
        popup = SettingSelectWindow(self, setting=self.setting)
        popup.grab_set()
        self.wait_window(popup)
        # replace the dropdown to consider updated information
        super().update()
