import tkinter

from appxf import logging

from kiss_cf.property import KissProperty
from .option_widget import OptionWidget

# TODO: rewrite to be based on PropertyDict

class OptionDictWidget(tkinter.Frame):
    '''Frame holding all configurable options for a section.

    Changes are directly applied to the configuration if they are valid.
    Consider using backup() on the config (not the frame) before starting this
    frame and providing a cancel button that uses restore() on the config.
    '''
    log = logging.getLogger(__name__ + '.OptionDictWidget')

    def __init__(self, parent: tkinter.Widget,
                 values: dict[str, str | bool | int] | None = None,
                 options: dict[str, KissProperty] | None = None,
                 **kwargs):

        super().__init__(parent, **kwargs)

        if values is None:
            values = {}
        if options is None:
            options = {}

        # TODO: this gave some conflicts. Better to aggregate something, here??
        self._kiss_values: dict[str, str] = {}
        self._kiss_options: dict[str, KissProperty] = {}
        # Ensure all values have an option:
        for option in values:
            if option in options:
                self._kiss_options[option] = options[option]
            else:
                self._kiss_options[option] = KissProperty.new(str)
        # Ensure all options have a value and convert values to string
        for option in options:
            if option in values:
                self._kiss_values[option] = \
                    self._kiss_options[option].to_string(
                    values[option])
            else:
                self._kiss_values[option] = ''

        self.log.debug(
            f'DictEditWidget for options: {self._kiss_options.keys()}')

        self._option_frames: list[OptionWidget] = []
        # option list should only contain configurable options
        option_list = [option
                       for option in self._kiss_options.keys()
                       if self._kiss_options[option].default_visibility]

        self.columnconfigure(0, weight=1)

        for iOption, option in zip(range(len(option_list)), option_list):
            self.log.debug(f'{iOption}: {option}')
            # option_frame = self.get_option_frame(frame, section, option)
            option_frame = OptionWidget(
                self, option,
                self._kiss_options[option],
                self._kiss_values[option])
            option_frame.grid(row=iOption, column=0, sticky='NWSE')
            self._option_frames.append(option_frame)

    def get_left_col_min_width(self) -> int:
        '''Get minimum width of left column.

        Can only be called after placing the widget (e.g. using grid()).
        Example:
            w = ConfigSectionWidget(root, config, section)
            w.grid(row=0, column=0)
            min_width = w.get_left_col_min_width()
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
            w = ConfigSectionWidget(root, config, section)
            w.grid(row=0, column=0)
            w.winfo_toplevel().update()
            w.adjust_left_columnwidth()
        '''
        min_size = self.get_left_col_min_width()
        self.set_left_column_min_width(min_size)

    def focus_curser_on_first_entry(self):
        if self._option_frames:
            self._option_frames[0].focus_set()

    @property
    def is_valid(self):
        is_valid = True
        for option_frame in self._option_frames:
            is_valid &= option_frame.is_valid
        return is_valid
