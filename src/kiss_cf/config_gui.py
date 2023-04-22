'''
Provide GUI classes for yagni_cft Config objects.
'''

import tkinter

from . import logging
from .config import Config
from .language import translate

# TODO: better option on when to validate input:
# https://www.plus2net.com/python/tkinter-validation.php


class EditConfigWindow(tkinter.Toplevel):
    log = logging.getLogger(__name__ + '.EditConfigWindow')

    def __init__(self, config: Config, section: str, title='Settings for {0}'):
        '''
        Create GUI window to edit a config section.

        Key title can be set to adjust language. Use {0} in string for section
        name (the string os passed to format()). The section name is translated
        using the configurations language dictionary. Example:
        EditConfigWindow(config, 'DATABASE', title='Einstellungen für {0}')
        '''
        super().__init__()

        guiRoot = self
        guiRoot.title(title.format(translate(config.language, section)))
        guiRoot.rowconfigure(1, weight=1)
        guiRoot.columnconfigure(0, weight=1)

        sectionFrame = ConfigSectionWidget(guiRoot, config, section)
        sectionFrame.grid(row=0, column=0, padx=0, pady=0, sticky='NSWE')
        sectionFrame.adjust_left_columnwidth()

        buttonFrame = tkinter.Frame(guiRoot)
        buttonFrame.rowconfigure(0, weight=1)
        buttonFrame.columnconfigure(0, weight=1)
        buttonFrame.columnconfigure(1, weight=1)
        buttonFrame.grid(row=1, column=0, sticky='NSEW')

        def cancelButtonFunction(event=None):
            self.log.debug('Cancel')
            config.restore()
            guiRoot.destroy()
        cancelButton = tkinter.Button(
            buttonFrame,
            text=translate(config.language, 'Cancel'),
            command=cancelButtonFunction)
        cancelButton.grid(row=0, column=0, padx=5, pady=5, sticky='SW')

        config.backup()

        def okButtonFunction(event=None):
            if sectionFrame.is_valid:
                self.log.debug('OK, storing config')
                config.store(section)
                guiRoot.destroy()
            else:
                self.log.debug('Cannot "OK", config not valid')
        okButton = tkinter.Button(
            buttonFrame,
            text=translate(config.language, 'OK'),
            command=okButtonFunction)
        okButton.grid(row=0, column=1, padx=5, pady=5, sticky='SE')

        guiRoot.bind('<Return>', okButtonFunction)
        guiRoot.bind('<KP_Enter>', okButtonFunction)


class ConfigSectionWidget(tkinter.Frame):
    '''Frame holding all configurable options for a section.

    Changes are directly applied to the configuration if they are valid.
    Consider using backup() on the config (not the frame) before starting this
    frame and providing a cancel button that uses restore() on the config.
    '''
    log = logging.getLogger(__name__ + '.ConfigSectionWidget')

    def __init__(self, parent: tkinter.Widget,
                 config: Config,
                 section: str,
                 **kwargs):

        self.log.debug(f'ConfigSectionWidget: {section}')
        super().__init__(parent, **kwargs)

        self._config = config
        self._section = section
        self._option_frames = list()

        # option list should only contain configurable options
        option_list = [option
                       for option in self._config.config.options(section)
                       if self._config.option_config[option].configurable]

        self.columnconfigure(0, weight=1)

        for iOption, option in zip(range(len(option_list)), option_list):
            self.log.debug(f'{iOption}: {option}')
            # option_frame = self.get_option_frame(frame, section, option)
            option_frame = ConfigOptionWidget(
                self, self._config, section, option)
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


class ConfigOptionWidget(tkinter.Frame):
    log = logging.getLogger(__name__ + '.ConfigOptionWidget')

    def __init__(self, parent,
                 config: Config,
                 section: str,
                 option: str,
                 **kwargs):
        self.log.debug(f'ConfigOptionWidget: {section}, {option}')

        super().__init__(parent, **kwargs)
        # import functoolsself.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.config = config
        self.section = section
        self.option = option
        self.option_config = config.option_config[option]

        self.label = tkinter.Label(self, justify='right')
        self.label.config(text=option)
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky='E')

        option = self.config.get(section, option)
        self.sv = tkinter.StringVar(self, option)
        self.sv.trace_add(
            'write', lambda var, index, mode: self.option_update())

        # TODO: derive width from option (settings)
        self.entry = tkinter.Entry(self, textvariable=self.sv, width=15)
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky='EW')

        self.is_valid = self.option_config.validate(self.sv.get())

    def focus_set(self):
        self.entry.focus_set()

    def option_update(self):
        value = self.sv.get()
        if self.option_config.validate(value):
            self.is_valid = True
            self.config.config[self.section][self.option] = value
            self.entry.config(foreground='black')
        else:
            self.is_valid = False
            self.entry.config(foreground='red')

    def color_entry(self, color):
        self.entry.configure('background', color)


class ConfigMenu(tkinter.Menu):
    '''Menu containing all configurable sections.'''

    def __init__(self, config: Config):
        super().__init__(tearoff=0)
        self._config = config

        for section in config.config.sections():
            if not config.section_config[section].configurable:
                break

            def command(section=section):
                window = EditConfigWindow(
                    self._config, section,
                    title='Settings for {0}')
                window.grab_set()
            self.add_command(label=section, command=command)
