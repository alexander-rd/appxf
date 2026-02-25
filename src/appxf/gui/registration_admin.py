# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
''' Providing GUI classes for user registration

- RegistrationUser is the user perspective for generating registration requests
  and loading responses (or initializing as admin).
- RegistrationAdmin is the admin perspective for reviewing requests, assigning
  roles, and generating responses.
'''
import tkinter
from tkinter import filedialog, messagebox

from appxf import logging
from appxf.gui.setting_dict import SettingDictColumnFrame, SettingDictSingleFrame
from appxf.registry import Registry
from appxf.setting import Setting, SettingDict

# TODO: This file is in DRAFT STATUS, mostly generated with GitHub copilot and
# needs a detailed review. Currently, getting the GUI and behavior right is
# prioritized since it may considerably impact this implementation.


class RegistrationAdmin:
    '''Provides admin-side registration GUI.

    Handles the admin perspective: loading registration requests,
    assigning roles,
    and generating responses. Window is created as Tk (root) if no parent is
    provided, or as Toplevel if parent is given. Expects registry to be
    initialized and current user to be admin.
    '''
    log = logging.getLogger(__name__ + '.RegistrationAdmin')

    def __init__(self,
                 registry: Registry,
                 user_config: SettingDict,
                 root_dir: str = './',
                 parent: tkinter.BaseWidget | None = None,
                 **kwargs):
        '''Initialize RegistrationAdmin and build GUI.

        Arguments:
            registry -- Initialized Registry instance (admin user required)
            root_dir -- Default directory for file dialogs
            parent -- Optional parent widget. If provided, window is Toplevel.
                      If None, window is Tk (root).
        '''
        self._registry = registry
        self._root_dir = root_dir
        self._parent = parent

        # GUI elements stored for access by action handlers
        self._admin_window: tkinter.Tk | tkinter.Toplevel | None = None
        # If provided, `user_config` is the SettingDict for user data
        self._user_config: SettingDict = user_config
        self._user_data_dict: SettingDict | None = None
        self._user_data_frame: SettingDictSingleFrame | None = None
        self._role_vars: dict[str, tkinter.BooleanVar] = {}
        self._current_request = None
        self._current_user_id: int | None = None

        # Build GUI now
        self._build_admin_gui()

    def show(self):
        '''Display the admin registration panel.'''
        if self._admin_window is None:
            return

        if self._parent is None:
            self._admin_window.mainloop()

    def _build_admin_gui(self):
        '''Build admin registration GUI with four sections.'''
        self.log.debug('Building admin registration panel')

        # Create root window (Tk) or toplevel depending on parent
        if self._parent is None:
            self._admin_window = tkinter.Tk()
            self._admin_window.title('User Registration - Admin Panel')
        else:
            self._admin_window = tkinter.Toplevel(self._parent)
            self._admin_window.title('Admin - Registration')

        # ==== SECTION 1: Action Buttons ====
        section1_frame = tkinter.LabelFrame(
            self._admin_window, text='Actions', padx=10, pady=10)
        section1_frame.pack(fill='x', padx=10, pady=10)

        gen_keys_btn = tkinter.Button(
            section1_frame,
            text='Generate Admin Keys',
            command=lambda: self._on_export_admin_keys(),
        )
        gen_keys_btn.pack(side=tkinter.LEFT, padx=5)

        load_req_btn = tkinter.Button(
            section1_frame,
            text='Load Registration Request',
            command=lambda: self._on_load_registration_request(),
        )
        load_req_btn.pack(side=tkinter.LEFT, padx=5)

        # ==== SECTION 2: User Data Display ====
        section2_frame = tkinter.LabelFrame(
            self._admin_window,
            text='User Data (from Request)',
            padx=10,
            pady=10,
        )
        section2_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Generate a user data SettingDict from the user config but using
        # default (empty) values.
        self._user_data_dict = SettingDict({
            key: Setting.new(self._user_config.get_setting(key).get_type())
            for key in self._user_config.keys()
            })

        self._user_data_frame = SettingDictSingleFrame(
            section2_frame,
            setting=self._user_data_dict)
        self._user_data_frame.pack(fill='both', expand=True)

        # ==== SECTION 3: Role Selection ====
        # Get available roles from registry
        available_roles = self._registry.get_roles()
        self._roles_setting_dict = SettingDict({
            role: (bool, role == 'user')
            for role in available_roles})

        section3_frame = SettingDictColumnFrame(
            parent=self._admin_window,
            frame_label='Assign Roles',
            setting=self._roles_setting_dict,
            columns=3)
        section3_frame.pack(fill='x', padx=10, pady=5)

        # ==== SECTION 4: Admin Action Buttons ====
        section4_frame = tkinter.Frame(self._admin_window)
        section4_frame.pack(fill='x', padx=10, pady=10)

        def on_close():
            '''Close the window.'''
            self._admin_window.destroy()

        def on_add_user():
            '''Add user to registry with selected roles.'''
            # Check that a request is loaded
            if self._current_request is None:
                messagebox.showwarning(
                    'No Request',
                    'Please load a registration request first',
                    parent=self._admin_window)
                return

            # Get selected roles from checkboxes
            selected_roles = [
                role for role in self._roles_setting_dict
                if self._roles_setting_dict[role]]
            self.log.debug('Selected roles: %s', selected_roles)

            try:
                # Add user to registry with selected roles
                user_id = self._registry.add_user_from_request(
                    self._current_request,
                    roles=selected_roles,
                )
                self.log.info(
                    'User added with ID: %s and roles: %s',
                    user_id,
                    selected_roles,
                )
                info_msg = (
                    f'User added successfully!\n'
                    f'User ID: {user_id}\n'
                    f'Roles: {", ".join(selected_roles)}'
                )
                messagebox.showinfo(
                    'Success',
                    info_msg,
                    parent=self._admin_window,
                )
                self._current_user_id = user_id
            except (ValueError, KeyError):
                self.log.exception('Failed to add user.')
                messagebox.showerror(
                    'Error',
                    'Failed to add user (see log for details).',
                    parent=self._admin_window,
                )

        def on_write_response():
            '''Write registration response to file.'''
            # Check that a user has been added
            if self._current_user_id is None:
                messagebox.showwarning(
                    'No User',
                    'Please add a user first before writing response',
                    parent=self._admin_window)
                return

            try:
                # Get response bytes from registry
                response_bytes = (
                    self._registry.get_response_bytes(
                        self._current_user_id
                    )
                )

                # Ask user where to save the file
                file_path = filedialog.asksaveasfilename(
                    parent=self._admin_window,
                    title='Save Registration Response',
                    defaultextension='.response',
                    filetypes=[
                        ('Response Files', '*.response'),
                        ('All Files', '*.*'),
                    ],
                    initialfile='registration.response',
                )

                if not file_path:
                    return  # User cancelled

                # Write response to file
                with open(file_path, 'wb') as f:
                    f.write(response_bytes)

                self.log.info('Response written to: %s', file_path)
            except (ValueError, KeyError, OSError) as e:
                self.log.error('Failed to write response: %s', e)
                messagebox.showerror(
                    'Error',
                    f'Failed to write response: {e}',
                    parent=self._admin_window)

        close_btn = tkinter.Button(
            section4_frame,
            text='Close',
            command=on_close,
            width=15,
        )
        close_btn.pack(side=tkinter.LEFT, padx=5)

        add_user_btn = tkinter.Button(
            section4_frame,
            text='Add User',
            command=on_add_user,
            width=15,
        )
        add_user_btn.pack(side=tkinter.LEFT, padx=5)

        write_resp_btn = tkinter.Button(
            section4_frame,
            text='Write Response',
            command=on_write_response,
            width=15,
        )
        write_resp_btn.pack(side=tkinter.LEFT, padx=5)

        if self._parent is None:
            self._admin_window.mainloop()

    def _on_export_admin_keys(self):
        '''Export admin keys to a file for distribution to new users.

        This calls `Registry.get_admin_key_bytes()` and writes the returned
        bytes to a file chosen by the admin.
        '''
        self.log.debug('_on_export_admin_keys called')

        # Ask user where to save admin key bytes
        file_path = filedialog.asksaveasfilename(
            parent=self._admin_window,
            title='Save Admin Keys',
            initialdir=self._root_dir,
            initialfile='admin.keys',
            defaultextension='.keys',
        )
        if not file_path:
            self.log.debug('Save admin keys cancelled by user')
            return

        key_bytes = self._registry.get_admin_key_bytes()

        try:
            with open(file_path, 'wb') as fh:
                fh.write(key_bytes)
        except (OSError, IOError) as e:
            self.log.error('Failed to write admin keys to %s: %s', file_path, e)
            messagebox.showerror(
                'Error', f'Failed to write file: {e}',
                parent=self._admin_window)
            return

        self.log.info('Admin keys saved to %s', file_path)

    def _on_load_registration_request(self):
        '''Load a registration request file and populate UI.'''
        file_path = filedialog.askopenfilename(
            parent=self._admin_window,
            title='Select Registration Request File',
            initialdir=self._root_dir,
            initialfile='registration.request',
            defaultextension='')
        if not file_path:
            return
        try:
            with open(file_path, 'rb') as fh:
                request_bytes = fh.read()
            # Parse and populate UI
            self._load_request_ui(request_bytes)
            self.log.info('Request loaded from %s', file_path)
        except (OSError, IOError) as e:
            self.log.error('Failed to read request file: %s', e)
            messagebox.showerror(
                'Error',
                f'Failed to read file: {e}',
                parent=self._admin_window)

    def _load_request_ui(self, request_bytes: bytes):
        '''Load and parse registration request, populate UI fields.

        Arguments:
            request_bytes -- Serialized registration request bytes
        '''

        try:
            request = self._registry.get_request_data(request_bytes)
        except (ValueError, KeyError) as e:
            self.log.error('Failed to parse registration request: %s', e)
            messagebox.showerror(
                'Error',
                f'Invalid request format: {e}',
                parent=self._admin_window)
            return

        # Store request for later use
        self._current_request = request

        # Populate user_data_dict with data from request.user_data
        if self._user_data_dict and self._user_data_frame:
            # Write values directly to the SettingDict
            for key in self._user_data_dict.keys():
                if key in request.user_data:
                    try:
                        self._user_data_dict[key] = request.user_data[key]
                        self.log.debug(
                            'Set %s = %s',
                            key,
                            request.user_data[key],
                        )
                    except (ValueError, KeyError) as e:
                        self.log.error('Failed to set %s: %s', key, e)

            # Update individual frames to reflect changed values
            for setting_frame in self._user_data_frame.frame_list:
                setting_frame.update()
        # with newly loaded user data, the user_id is unknown again:
        self._current_user_id = None

        self.log.debug('Request user data: %s', request.user_data)
