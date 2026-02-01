'''
Provide GUI classes for yagni_cft Config objects.
'''

import tkinter
from appxf.logging import logging

from appxf_private.config import Config
from appxf_private.registry import Registry

from appxf_private.gui import manual_config_update
from appxf_private.gui.setting_dict import SettingDictWindow
from appxf_private.gui.locale import _
from appxf_private.gui.registration_admin import RegistrationAdmin

# TODO: better option on when to validate input:
# https://www.plus2net.com/python/tkinter-validation.php


class ConfigMenu(tkinter.Menu):
    '''Menu for Configuration Options and User Database'''
    log = logging.getLogger(__name__ + '.ConfigMenu')

    def __init__(
            self,
            parent: tkinter.Tk,
            config: Config,
            registry: Registry | None = None,
            root_path: str = '.',
            **kwargs):
        super().__init__(parent, tearoff=0, **kwargs)
        self._parent = parent
        self._config = config
        self._registry = registry
        self._root_path = root_path

        self.add_config_sections()
        self.add_registry_items()

    def add_config_sections(self):
        for section in self._config.sections:
            if not self._config.section(section).options.visible:
                break

            def command(section=section):
                window = SettingDictWindow(
                    self._parent,
                    title=f'Settings for {section}',
                    setting=self._config.section(section),
                    )
                window.grab_set()
            self.add_command(label=section, command=command)

    def add_registry_items(self):
        if self._registry is None:
            return

        if not self._registry.try_load():
            self.log.warning(
                'Registry object provided to ConfigMenu but not initialized.'
                'Consider using Login, RegistrationUser and RegistrationAdmin '
                'GUIs to prepare and unlock Security and Registry objects '
                'before launching the GUI of your application.')
            return

        self.add_separator()

        # Adding options for USERs
        def load_config_update():
            manual_config_update.handle_manual_config_update_load(
                parent=self._parent,
                registry=self._registry,
                initial_path=self._root_path)
            # TODO #43: Unfortunately, if anything in this operation goes
            # wrong, there is no communication path, yet. If input would
            # contain a frame with status, that one could be used for updates.

        self.add_command(
            label=_('menu', 'Load Config Update'),
            command=load_config_update)


        if 'admin' in self._registry.get_roles(user_id=0):
            def write_config_update():
                manual_config_update.handle_manual_config_update_write(
                    parent=self._parent,
                    registry=self._registry,
                    initial_path=self._root_path)

                # TODO #44: An option is missing to set the
                # to-be-exported-sections. Actually, credentials that are not
                # required for particular roles should NOT be exported to them.
                # .. BUT .. config sections have no such information attached.
                # >> It's almost a general storable feature for which roles a
                # file should be available (and a config section IS a
                # storable). By default, config sections would be shared with
                # all users.
                #
                # How to deal with this detail on config file updates? That
                # would be like (1) ALL config sections being encrypted, (2)
                # the keys are accumulated per role and then hybrid-encrypted
                # for the users of that role. Main difference is [hybrid
                # encryption of all sections at once] versus [separate
                # symmetric encryption of sections] + [hybrid encryption for
                # each role] + [packing all in ONE file].
                #
                # Note how this approach is SIMILAR to my last comment just
                # before Registry class on updates in SharedStorage (see also
                # #42).
                #
                # Interesting detail: I handle manual config updates. Manual
                # file updates could be handled quite analogously. What are
                # sections in the discussion above would be registered files of
                # a FileLocation (or a set of FileLocations).
            self.add_command(
                label=_('menu', 'Write Config Update'),
                command=write_config_update)

            # Add user registration menu
            def open_user_registration():
                registration = RegistrationAdmin(
                    registry=self._registry,
                    root_dir=self._root_path,
                    user_config=self._config.section('USER'))
                registration.show()

            self.add_command(
                label=_('menu', 'User Registration'),
                command=open_user_registration)
