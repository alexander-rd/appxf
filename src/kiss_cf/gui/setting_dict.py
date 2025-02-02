''' Aggregate single setting frames/windows into one interface

This module handles, in particular, SettingDict but aggregates all setting_*
modules.
'''
from typing import Any, Mapping, Iterable, TypeAlias
import tkinter
import math

from appxf import logging
from kiss_cf.setting import SettingBool, Setting, SettingDict, SettingSelect

from .common import AppxfGuiError, FrameWindow, GridFrame
from .setting_base import SettingFrameBase, SettingFrameBool, SettingFrameDefault
from .setting_select import SettingSelectFrame

# TODO: There is a matter of style open for displaying settings in a column.
# Should the labels be aligned or should the space rather be used for entries.
# What's the default setting and how to adjust?

SettingInput: TypeAlias = (Setting | SettingDict |
                           dict[str, Any] | Iterable[Setting])

def get_single_setting_frame(parent: tkinter.BaseWidget,
                             setting: Setting,
                             **kwargs) -> SettingFrameBase:
    if isinstance(setting, SettingSelect):
        return SettingSelectFrame(
            parent=parent,
            setting=setting,
            **kwargs)
    if isinstance(setting, SettingBool):
        return SettingFrameBool(
            parent=parent,
            setting=setting,
            **kwargs)
    return SettingFrameDefault(
            parent=parent,
            setting=setting,
            **kwargs)

def input_type_to_setting_dict(setting: SettingInput) -> SettingDict:
    ''' Convert allowed compound setting inputs to a SettingDict'''

    if isinstance(setting, SettingDict):
        return setting
    # The following two should also not already be a setging dict (which is
    # Iterable and Mapping). Dictionaries of settings are cast into a
    # SettingDict object:
    if isinstance(setting, Mapping):
        # Typing is ignored below since an Iterable[AppxfSetting] could
        # theoretically be a Mapping[AppxfSetting, Unknown] which would also
        # end up here. This is invalid input and not cought here.
        return SettingDict(data=setting) # type: ignore
    # iterables of settings are also handled like SettingDict
    if isinstance(setting, Iterable) and not isinstance(setting, Mapping):
        return SettingDict(data={
            this_setting.name: this_setting for this_setting in setting
            })

    if isinstance(setting, Setting):
        return SettingDict(data={setting.name: setting})

    raise AppxfGuiError(f'Input type unknown: {setting.__class__.__name__}')


class SettingDictSingleFrame(SettingFrameBase):
    '''Frame holding PropertyWidgets for a dictionary of KissProperty.

    Changes are directly applied to the properties if they are valid. Consider
    using backup() on the properties before starting this frame and
    providing a cancel button that uses restore() on the config.
    '''
    log = logging.getLogger(__name__ + '.SettingDictFrame')

    def __init__(self, parent: tkinter.BaseWidget,
                 setting: SettingInput,
                 **kwargs):

        super().__init__(parent, **kwargs)
        setting = input_type_to_setting_dict(setting)

        # strip properties from the dict that are not mutable:
        self.setting_dict = {key: setting.get_setting(key)
                             for key in setting.keys()
                             if setting.get_setting(key).mutable}

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
        self.frame_list: list[SettingFrameBase] = []
        for key in self.setting_dict.keys():
            self._place_setting_frame(
                setting.get_setting(key),
                element_gui_options.get(key, {}))

    def _place_setting_frame(self, setting: Setting, gui_options):
        if 'frame_type' in gui_options:
            setting_frame = gui_options['frame_type'](
                self, setting, gui_options)
        setting_frame = get_single_setting_frame(self, setting, **gui_options)
        self.place(setting_frame, row=len(self.frame_list), column=0)
        # apply row weight from underlying frame:
        self.rowconfigure(len(self.frame_list), weight=setting_frame.get_total_row_weight())

        self.frame_list.append(setting_frame)

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
        for i_row in range(n_rows):
            # Get the ConfigOptionWidget of the row
            config_option_widget = self.grid_slaves(row=i_row, column=0)[0]
            # get the label
            label_widget = config_option_widget.grid_slaves(row=0, column=0)[0]
            # get label size
            size = label_widget.winfo_width()
            # update min size
            if size > min_size:
                min_size = size
        # we can simply add 10 here since we know the hard coded
        # padding.
        return min_size + 10

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
        for setting_frame in self.frame_list:
            valid &= setting_frame.is_valid()
        return valid


class SettingDictColumnFrame(SettingFrameBase):
    def __init__(self, parent: tkinter.BaseWidget,
                 setting: SettingInput,
                 columns: int,
                 kiss_options: dict | None = None,
                 **kwargs):
        # kwargs is NOT passed down to THIS frame. It will be passed down to
        # the column frames. This is hopefully more likely what a user might
        # want.
        super().__init__(parent)
        setting = input_type_to_setting_dict(setting)

        if kiss_options is None:
            kiss_options = {}

        key_list = list(setting.keys())
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
            prop_dict_list[key_to_sub_dict[i]].add({key: setting.get_setting(key)})

        # build up frames
        self.frame_list: list[SettingDictSingleFrame] = []
        max_row_weight_over_columns = 0
        for prop_dict in prop_dict_list:
            self.columnconfigure(len(self.frame_list), weight=1)
            this_frame = SettingDictSingleFrame(
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
    ''' Display dialog for Settings or Setting dicts '''
    log = logging.getLogger(__name__ + '.SettingDictWindow')

    def __init__(self, parent,
                 title: str,
                 setting: Setting | SettingDict,
                 kiss_options: dict | None = None,
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
        # Whole class operated on SettingDict and a single setting is just cast
        # up to a SettingDict to handle it (required to obtain store/load
        # behavior for backup&restore upon cancel)
        if isinstance(setting, Setting):
            self.property_dict = SettingDict(data={setting.name: setting})
        elif isinstance(setting, SettingDict):
            self.property_dict = setting
        else:
            raise AppxfGuiError(f'Setting must be AppxfSetting or SettingDict '
                                f'but is {type(setting)}')
        # Ensure values are stored. If congiuration fails, values will be reloaded.
        self.property_dict.store()

        columns = kiss_options.get('columns', 1)
        if columns <= 1:
            self.dict_frame = SettingDictSingleFrame(
                self, self.property_dict, row_spread=True, **kiss_options)
        else:
            self.dict_frame = SettingDictColumnFrame(
                self, self.property_dict, columns, kiss_options, row_spread=True)
        self.place_frame(self.dict_frame)
        self.update()
        self.dict_frame.adjust_left_columnwidth()

        self.bind('<<Cancel>>', lambda event: self._handle_cancel_button())
        self.bind('<<OK>>', lambda event: self._handle_ok_button())

    def _handle_ok_button(self):
        self.log.debug('OK')
        if self.dict_frame.is_valid():
            self.property_dict.store()
            self.destroy()
        else:
            self.log.debug('Cannot "OK", config not valid')

    def _handle_cancel_button(self):
        self.log.debug('Cancel')
        self.property_dict.load()
        self.destroy()
