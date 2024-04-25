'''
Provide GUI classes for KissProperty objects.
'''

import tkinter
import math

from appxf import logging
from kiss_cf.language import translate
from kiss_cf.setting import SettingDict, AppxfSetting, AppxfBool


# TODO: better option on when to validate input:
# https://www.plus2net.com/python/tkinter-validation.php

# TODO: Class naming is a mess

# TODO: GUI options handling does not seem to be very straight

# TODO: Documentation of options

# TODO: the above suggests: larger review and rework


class PropertyWidget(tkinter.Frame):
    '''Frame holding a single property.'''
    log = logging.getLogger(__name__ + '.PropertyWidget')

    def __init__(self, parent,
                 label: str,
                 property: AppxfSetting,
                 **kwargs):
        super().__init__(parent, **kwargs)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.property = property

        self.label = tkinter.Label(self, justify='right')
        self.label.config(text=label)
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky='NE')

        value = str(self.property.value)
        self.sv = tkinter.StringVar(self, value)
        self.sv.trace_add(
            'write', lambda var, index, mode: self.value_update())

        # TODO: have width from some input
        self.entry = tkinter.Entry(self, textvariable=self.sv, width=15)
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky='NEW')

    def is_valid(self):
        return self.property.validate(self.sv.get())

    def focus_set(self):
        self.entry.focus_set()

    def value_update(self):
        value = self.sv.get()
        valid = self.property.validate(value)
        if valid:
            self.property.value = value
            self.entry.config(foreground='black')
        else:
            self.entry.config(foreground='red')


class BoolCheckBoxWidget(tkinter.Frame):
    '''CheckBox frame for a single boolean.'''
    log = logging.getLogger(__name__ + '.BoolCheckBoxWidget')

    def __init__(self, parent,
                 property: AppxfSetting,
                 label: str,
                 kiss_options: dict = dict(),
                 **kwargs):
        super().__init__(parent, **kwargs)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.property = property

        self.label = tkinter.Label(self, justify='right')
        self.label.config(text=label)
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky='NE')

        self.iv = tkinter.IntVar(self, value=self.property.value)

        # TODO: have width from some input
        self.checkbox = tkinter.Checkbutton(self, text='', variable=self.iv)
        self.checkbox.grid(row=0, column=1, padx=5, pady=5, sticky='NW')

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


class PropertyDictWidget(tkinter.Frame):
    '''Frame holding PropertyWidgets for a dictionary of KissProperty.

    Changes are directly applied to the properties if they are valid. Consider
    using backup() on the properties before starting this frame and
    providing a cancel button that uses restore() on the config.
    '''
    log = logging.getLogger(__name__ + '.PropertyDictWidget')

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
        self.frame_list = list()
        for key in self.property_dict.keys():
            self._place_property_frame(
                property_dict.get_setting(key), key,
                element_gui_options.get(key, dict()))

    def _place_property_frame(self, prop: AppxfSetting, label, gui_options):
        self.rowconfigure(len(self.frame_list), weight=1)

        if 'frame_type' in gui_options:
            property_frame = gui_options['frame_type'](
                self, prop, label, gui_options)
        elif isinstance(prop, AppxfBool):
            property_frame = BoolCheckBoxWidget(
                self, prop, label, gui_options)
        else:
            property_frame = PropertyWidget(
                self, label, prop, **gui_options)
        property_frame.grid(
            row=len(self.frame_list), column=0, sticky='NWSE')
        self.frame_list.append(property_frame)

    def get_left_col_min_width(self) -> int:
        '''Get minimum width of left column.

        Can only be called after placing the widget (e.g. using grid()).
        Example:
        ```
            w = PropertyDictWidget(root, property_dict)
            w.grid(row=0, column=0)
            min_width = w.get_left_col_min_width()
        ```
        '''
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
            w = PropertyDictWidget(root, property_dict)
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

    def is_valid(self):
        valid = True
        for property_frame in self.frame_list:
            valid &= property_frame.is_valid()
        return valid


class PropertyDictColumnFrame(tkinter.Frame):
    def __init__(self, parent: tkinter.BaseWidget,
                 property_dict: SettingDict,
                 columns: int,
                 kiss_options: dict = dict(),
                 **kwargs):
        # kwargs is NOT passed down to THIS frame. It will be passed down to
        # the column frames. This is hopefully more likely what a user might
        # want.
        super().__init__(parent)

        key_list = list(property_dict.keys())
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
            prop_dict_list[key_to_sub_dict[i]].add({key: property_dict[key]})

        # build up frames
        self.frame_list: list[PropertyDictWidget] = []
        for prop_dict in prop_dict_list:
            self.columnconfigure(len(self.frame_list), weight=1)
            this_frame = PropertyDictWidget(
                self, prop_dict, **kwargs)
            this_frame.grid(
                row=0, column=len(self.frame_list), sticky='NWSE')
            self.frame_list.append(this_frame)

    def adjust_left_columnwidth(self):
        for frame in self.frame_list:
            frame.adjust_left_columnwidth()

    def focus_set(self):
        self.frame_list[0].focus_set()

    def valid(self):
        valid = True
        for frame in self.frame_list:
            valid &= frame.is_valid()
        return valid


class EditPropertyDictWindow(tkinter.Toplevel):
    log = logging.getLogger(__name__ + '.EditPropertyDictWindow')

    def __init__(self, parent,
                 title: str,
                 property_dict: SettingDict,
                 kiss_options: dict = dict(),
                 **kwargs):
        '''
        Create GUI window to edit a dictionary of properties.
        '''
        super().__init__(parent, **kwargs)
        self.property_dict = property_dict
        # Ensure values are stored. If congiuration fails, values will be reloaded.
        self.property_dict.store()
        # TODO: the above strategy will not work for a config that may use
        # StorageDummy since no real backup is generated. Proposal: the dummy
        # shall store in RAM and the dummy shall be renamed accordingly.

        self.language = dict()

        self.title(title)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        columns = kiss_options.get('columns', 1)
        if columns <= 1:
            property_frame = PropertyDictWidget(
                self, property_dict, **kiss_options)
        else:
            property_frame = PropertyDictColumnFrame(
                self, property_dict, columns, kiss_options)
        property_frame.grid(row=0, column=0, padx=0, pady=0, sticky='NSWE')
        self.update()
        property_frame.adjust_left_columnwidth()

        button_frame = tkinter.Frame(self)
        button_frame.rowconfigure(0, weight=1)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.grid(row=1, column=0, sticky='NSEW')

        def cancelButtonFunction(event=None):
            self.log.debug('Cancel')
            self.property_dict.load()
            self.destroy()
        cancelButton = tkinter.Button(
            button_frame,
            text=translate(self.language, 'Cancel'),
            command=cancelButtonFunction)
        cancelButton.grid(row=0, column=0, padx=5, pady=5, sticky='SW')

        def okButtonFunction(event=None):
            if property_frame.is_valid():
                self.log.debug('OK')
                self.property_dict.store()
                self.destroy()
            else:
                self.log.debug('Cannot "OK", config not valid')
        okButton = tkinter.Button(
            button_frame,
            text=translate(self.language, 'OK'),
            command=okButtonFunction)
        okButton.grid(row=0, column=1, padx=5, pady=5, sticky='SE')

        self.bind('<Return>', okButtonFunction)
        self.bind('<KP_Enter>', okButtonFunction)
        # cancel action must also apply on window close
        self.protocol('WM_DELETE_WINDOW', cancelButtonFunction)
