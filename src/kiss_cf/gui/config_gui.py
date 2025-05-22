'''
Provide GUI classes for yagni_cft Config objects.
'''

import tkinter

from appxf import logging
from kiss_cf.gui.setting_dict import SettingDictWindow
from kiss_cf.config import Config

# TODO: reconsider language concept: maybe something configurable, working on
# human readable INI files and adding a context (section, option, button, ...)
# to the translations.
#
# from ..language import translate

# TODO: better option on when to validate input:
# https://www.plus2net.com/python/tkinter-validation.php

class ConfigMenu(tkinter.Menu):
    '''Menu containing all configurable sections.'''

    def __init__(self, parent: tkinter.Tk, config: Config, **kwargs):
        super().__init__(tearoff=0, **kwargs)
        self._config = config

        for section in config.sections:
            if not config.section(section).default_visibility:
                break

            def command(section=section):
                window = SettingDictWindow(parent,
                    title=f'Settings for {section}',
                    setting=self._config.section(section),
                    )
                window.grab_set()
            self.add_command(label=section, command=command)
