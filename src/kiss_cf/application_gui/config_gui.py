'''
Provide GUI classes for yagni_cft Config objects.
'''

import tkinter

from kiss_cf import logging
from kiss_cf.gui.option_dict_widget import OptionDictWidget
from kiss_cf.config import Config

# TODO: reconsider language concept: maybe something configurable, working on
# human readable INI files and adding a context (section, option, button, ...)
# to the translations.
#
# from ..language import translate

# TODO: better option on when to validate input:
# https://www.plus2net.com/python/tkinter-validation.php


class EditConfigWindow(tkinter.Toplevel):
    log = logging.getLogger(__name__ + '.EditConfigWindow')

    def __init__(self,
                 config: Config,
                 section: str,
                 title='Settings for {0}',
                 **kwargs):
        '''
        Create GUI window to edit a config section.

        Key title can be set to adjust language. Use {0} in string for section
        name (the string os passed to format()). The section name is translated
        using the configurations language dictionary. Example:
        EditConfigWindow(config, 'DATABASE', title='Einstellungen für {0}')
        '''
        super().__init__(**kwargs)

        gui_root = self
        # TODO: all commented out lines with ".language"
        # guiRoot.title(title.format(translate(config.language, section)))
        gui_root.title(title.format(section))
        gui_root.rowconfigure(1, weight=1)
        gui_root.columnconfigure(0, weight=1)

        config_section = config.section(section)
        sectionFrame = OptionDictWidget(
            gui_root,
            values=config_section.get_all(copy=True),
            options=config_section.options)
        sectionFrame.grid(row=0, column=0, padx=0, pady=0, sticky='NSWE')
        sectionFrame.adjust_left_columnwidth()

        buttonFrame = tkinter.Frame(gui_root)
        buttonFrame.rowconfigure(0, weight=1)
        buttonFrame.columnconfigure(0, weight=1)
        buttonFrame.columnconfigure(1, weight=1)
        buttonFrame.grid(row=1, column=0, sticky='NSEW')

        def cancelButtonFunction(event=None):
            self.log.debug('Cancel')
            gui_root.destroy()
        cancelButton = tkinter.Button(
            buttonFrame,
            # text=translate(config.language, 'Cancel'),
            text='Cancel',
            command=cancelButtonFunction)
        cancelButton.grid(row=0, column=0, padx=5, pady=5, sticky='SW')

        def okButtonFunction(event=None):
            if sectionFrame.is_valid:
                self.log.debug('OK, storing config')
                # TODO: set values into config
                config.section(section).store()
                gui_root.destroy()
            else:
                self.log.debug('Cannot "OK", config not valid')
        okButton = tkinter.Button(
            buttonFrame,
            # text=translate(config.language, 'OK'),
            text='OK',
            command=okButtonFunction)
        okButton.grid(row=0, column=1, padx=5, pady=5, sticky='SE')

        gui_root.bind('<Return>', okButtonFunction)
        gui_root.bind('<KP_Enter>', okButtonFunction)


class ConfigMenu(tkinter.Menu):
    '''Menu containing all configurable sections.'''

    def __init__(self, config: Config, **kwargs):
        super().__init__(tearoff=0, **kwargs)
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
