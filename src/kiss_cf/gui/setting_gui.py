'''
Provide GUI classes for KissProperty objects.
'''

import tkinter
import math
from typing import Callable

from appxf import logging
from kiss_cf.language import translate
from kiss_cf.setting import SettingDict, AppxfSetting, AppxfBool

from .common import GridFrame, FrameWindow, GridSetting

# TODO: better option on when to validate input:
# https://www.plus2net.com/python/tkinter-validation.php

# TODO: Class naming is a mess

# TODO: GUI options handling does not seem to be very straight

# TODO: Documentation of options

# TODO: the above suggests: larger review and rework

# TODO: There is an abstract SettingFrame missing which could be configured as
#       default for a setting.


class SettingFrame(GridFrame):
    '''Frame holding a single property.'''
    log = logging.getLogger(__name__ + '.PropertyWidget')

    def __init__(self, parent,
                 setting: AppxfSetting,
                 **kwargs):
        super().__init__(parent, **kwargs)

        print(f'Setting frame for {setting.name}')

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


class BoolCheckBoxFrame(GridFrame):
    '''CheckBox frame for a single boolean.'''
    log = logging.getLogger(__name__ + '.BoolCheckBoxWidget')

    def __init__(self, parent,
                 setting: AppxfSetting,
                 kiss_options: dict = dict(),
                 **kwargs):
        super().__init__(parent, **kwargs)

        self.rowconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

        self.property = setting

        self.label = tkinter.Label(self, justify='right')
        self.label.config(text=setting.name + ':')
        self.place(self.label, row=0, column=0)

        self.iv = tkinter.IntVar(self, value=self.property.value)

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
        self.property.value = self.iv.get()


class SettingDictFrame(GridFrame):
    '''Frame holding PropertyWidgets for a dictionary of KissProperty.

    Changes are directly applied to the properties if they are valid. Consider
    using backup() on the properties before starting this frame and
    providing a cancel button that uses restore() on the config.
    '''
    log = logging.getLogger(__name__ + '.SettingDictFrame')

    def __init__(self, parent: tkinter.BaseWidget,
                 property_dict: SettingDict,
                 **kwargs):

        super().__init__(parent, **kwargs)

        # strip proerties from the dict that are not mutable:
        self.property_dict = {key: property_dict[key]
                              for key in property_dict.keys()
                              if property_dict.get_setting(key).mutable}

        # TODO: the above should be applied according to default_visibility.
        # Not mutable should still be displayed but grayed out or not editable.

        self.columnconfigure(0, weight=1)
        # rowconfigure in the loop below

        # TODO: element_gui_options does not do anything anymore. Given the
        # usage in _place_property_frame() it was intended to  allow
        # overwriting the usage of checkboxes for booleans. Once the remarks on
        # default_visibility are resolved, the new concept may incorporate this
        # setting as well.
        element_gui_options = {}
        self.frame_list: list[SettingFrame] = []
        for key in self.property_dict.keys():
            self._place_property_frame(
                property_dict.get_setting(key),
                element_gui_options.get(key, {}))

    def _place_property_frame(self, prop: AppxfSetting, gui_options):
        if 'frame_type' in gui_options:
            property_frame = gui_options['frame_type'](
                self, prop, gui_options)
        elif isinstance(prop, AppxfBool):
            property_frame = BoolCheckBoxFrame(
                self, prop, gui_options)
        else:
            property_frame = SettingFrame(
                self, prop, **gui_options)
        self.place(property_frame, row=len(self.frame_list), column=0)
        # apply row weight from underlying frame:
        self.rowconfigure(len(self.frame_list), weight=property_frame.get_total_row_weight())

        self.frame_list.append(property_frame)

    def get_left_col_min_width(self) -> int:
        '''Get minimum width of left column.

        Can only be called after placing the widget (e.g. using grid()).
        Example:
        ```
            w = SettingDictFrame(root, property_dict)
            w.grid(row=0, column=0)
            min_width = w.get_left_col_min_width()
        ```
        '''
        # TODO: docstring above is not correct anymore after grid() is
        # substituted by place(). When touching this, I may reconsider
        # overwriting grid() (and pack() and the other placing mechanisms).
        # There is no need for a new naming.
        self.winfo_toplevel().update()
        n_rows = self.grid_size()[1]
        # get minimum size
        min_size = 0
        for iRow in range(n_rows):
            # Get the ConfigOptionWidget of the row
            config_option_widget = self.grid_slaves(row=iRow, column=0)[0]
            # get the label
            label_widget = config_option_widget.grid_slaves(row=0, column=0)[0]
            # get label size
            size = label_widget.winfo_width()
            # update min size
            if size > min_size:
                min_size = size
        # we can simply add 10 here since we know the hard coded
        # padding.
        return (min_size + 10)

    def set_left_column_min_width(self, width: int):
        n_rows = self.grid_size()[1]
        for iRow in range(n_rows):
            widgets = self.grid_slaves(row=iRow, column=0)
            for widget in widgets:
                widget.columnconfigure(0, minsize=width)

    def adjust_left_columnwidth(self):
        '''Get left labels aligned.

        Can only be called after placing the widget (e.g. using grid()). You
        also need to update the root before doing so. Example:
        ```
            w = SettingDictFrame(root, property_dict)
            w.grid(row=0, column=0)
            w.winfo_toplevel().update()
            w.adjust_left_columnwidth()
        ```
        '''
        min_size = self.get_left_col_min_width()
        self.set_left_column_min_width(min_size)

    def focus_curser_on_first_entry(self):
        if self.frame_list:
            self.frame_list[0].focus_set()

    def is_valid(self) -> bool:
        valid = True
        for property_frame in self.frame_list:
            valid &= property_frame.is_valid()
        return valid


class SettingDictColumnFrame(GridFrame):
    def __init__(self, parent: tkinter.BaseWidget,
                 setting_dict: SettingDict,
                 columns: int,
                 kiss_options: dict = None,
                 **kwargs):
        # kwargs is NOT passed down to THIS frame. It will be passed down to
        # the column frames. This is hopefully more likely what a user might
        # want.
        super().__init__(parent)

        if kiss_options is None:
            kiss_options = {}

        key_list = list(setting_dict.keys())
        direction = kiss_options.get('column_direction', 'down')
        if direction == 'down':
            items_per_col = math.ceil(len(key_list)/columns)
            key_to_sub_dict = [int(i/items_per_col)
                               for i in range(len(key_list))]
        elif direction == 'right':
            key_to_sub_dict = [i % columns
                               for i in range(len(key_list))]
        else:
            raise ValueError(
                f'"column_direction" only supports "down" or '
                f'"right", you provided "{direction}"')

        # fill property dictionaries
        prop_dict_list = [SettingDict() for i in range(columns)]
        for i, key in enumerate(key_list):
            prop_dict_list[key_to_sub_dict[i]].add({key: setting_dict[key]})

        # build up frames
        self.frame_list: list[SettingDictFrame] = []
        max_row_weight_over_columns = 0
        for prop_dict in prop_dict_list:
            self.columnconfigure(len(self.frame_list), weight=1)
            this_frame = SettingDictFrame(
                self, prop_dict, **kwargs)
            self.place(this_frame, row=0, column=len(self.frame_list))
            self.frame_list.append(this_frame)
            if this_frame.get_total_row_weight() > max_row_weight_over_columns:
                max_row_weight_over_columns = this_frame.get_total_row_weight()
        # column weights are configured above in the for loop. The weight of
        # the one row containing all columns equals the maximum row weight of
        # the columns. If no column needs vertical resizing, this ColumnFrame
        # would also not need resizing. If a single row needs resizing, the
        # other settings would spread out likewise.
        self.rowconfigure(0, weight=max_row_weight_over_columns)

    def adjust_left_columnwidth(self):
        for frame in self.frame_list:
            frame.adjust_left_columnwidth()

    def focus_set(self):
        self.frame_list[0].focus_set()

    def is_valid(self):
        valid = True
        for frame in self.frame_list:
            valid &= frame.is_valid()
        return valid


class SettingDictWindow(FrameWindow):
    log = logging.getLogger(__name__ + '.SettingDictWindow')

    def __init__(self, parent,
                 title: str,
                 setting_dict: SettingDict,
                 kiss_options: dict = None,
                 **kwargs):
        '''
        Create GUI window to edit a dictionary of properties.
        '''
        super().__init__(parent,
                         title=title,
                         buttons=['Cancel', 'OK'],
                         key_enter_as_button='OK',
                         **kwargs)
        if kiss_options is None:
            kiss_options = {}
        self.property_dict = setting_dict
        # Ensure values are stored. If congiuration fails, values will be reloaded.
        self.property_dict.store()

        columns = kiss_options.get('columns', 1)
        if columns <= 1:
            self.dict_frame = SettingDictFrame(
                self, setting_dict, row_spread=True, **kiss_options)
        else:
            self.dict_frame = SettingDictColumnFrame(
                self, setting_dict, columns, kiss_options, row_spread=True)
        self.place_frame(self.dict_frame)
        self.update()
        self.dict_frame.adjust_left_columnwidth()

        self.bind('<<Cancel>>', lambda event: self.handle_cancel_button())
        self.bind('<<OK>>', lambda event: self.handle_ok_button())

    def handle_ok_button(self):
        self.log.debug('OK')
        if self.dict_frame.is_valid():
            self.property_dict.store()
            self.destroy()
        else:
            self.log.debug('Cannot "OK", config not valid')

    def handle_cancel_button(self):
        self.log.debug('Cancel')
        self.property_dict.load()
        self.destroy()
