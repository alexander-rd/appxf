''' Providing GUI classes for user registration

- RegistrationUser is the user perspective for generating registration requests
  and loading responses (or initializing as admin).
- RegistrationAdmin is the admin perspective for reviewing requests, assigning
  roles, and generating responses.
'''
import tkinter
import tkinter.ttk
from tkinter import filedialog, messagebox

from appxf import logging
from kiss_cf.registry import Registry
from kiss_cf.setting import Setting, SettingDict
from kiss_cf.gui.setting_dict import SettingDictSingleFrame

# TODO: This file is in DRAFT STATUS, mostly generated with GitHub copilot and
# needs a detailed review. Currently, getting the GUI and behavior right is
# prioritized since it may considerably impact this implementation.


class RegistryAbortError(Exception):
    '''Used when user aborts the registry process.'''


class RegistrationUser:
    '''User-side registration GUI

    Handles the user perspective: generating registration requests and loading
    responses (or initializing as admin). Window is created as Tk (root) if no
    parent is provided, or as Toplevel if parent is given.
    '''
    log = logging.getLogger(__name__ + '.RegistrationUser')

    def __init__(self,
                 registry: Registry,
                 root_dir: str = './',
                 parent: tkinter.BaseWidget | None = None,
                 **kwargs):
        '''Initialize RegistrationUser and build GUI.

        Arguments:
            registry -- Registry instance
            root_dir -- Default directory for file dialogs
            parent -- Optional parent widget. If provided, window is Toplevel.
                      If None, window is Tk (root).
        '''
        super().__init__(**kwargs)
        self._registry = registry
        self._root_dir = root_dir
        self._parent = parent
        self._gui_root: tkinter.Tk | tkinter.Toplevel | None = None

        # Build GUI now
        self._build_user_gui()

        # TODO: How check(), __init__ and _show_user_gui work together does not
        # seem to be nice. In particular, the GUI woulid be build even though
        # the check may not require it, consuming time while not required.
        # However, it is not clear if this GUI may be required when the user
        # wants to (needs to?) generate a request even though the user is
        # already registered. Upon problems in config data? Upon re-generation
        # of keys??

    def check(self) -> bool:
        ''' Check and return registration status, using GUI when needed '''
        if not self._registry.is_initialized():
            self._show_user_gui()
        return self._registry.is_initialized()

    def _show_user_gui(self):
        '''Display the user registration GUI.'''
        if self._gui_root is None:
            return

        if self._parent is None:
            self._gui_root.mainloop()

    def _build_user_gui(self):
        '''Build user registration GUI with three frames.'''
        # Create root window (Tk) or toplevel depending on parent
        if self._parent is None:
            self._gui_root = tkinter.Tk()
            self._gui_root.title('Registry - User Registration')
        else:
            self._gui_root = tkinter.Toplevel(self._parent)
            self._gui_root.title('User Registration')

        self._gui_root.rowconfigure(0, weight=1)
        self._gui_root.rowconfigure(1, weight=0)
        self._gui_root.rowconfigure(2, weight=0)
        self._gui_root.columnconfigure(0, weight=1)

        # Frame 1: Registration Request Data (User Data)
        #request_frame_label = tkinter.Label(self._gui_root, text='Registration Request Data')
        #request_frame_label.grid(row=0, column=0, sticky='NW', padx=5, pady=5)

        # request_data = SettingDict()
        # Placeholder: in real usage this would come from the registry's user config
        #request_frame = SettingDictSingleFrame(self._gui_root, setting=request_data)
        #request_frame.grid(row=0, column=0, sticky='NSWE', padx=5, pady=5)

        #sep1 = tkinter.ttk.Separator(self._gui_root, orient='horizontal')
        #sep1.grid(row=1, column=0, sticky='WE')

        # Frame 3: Action Buttons
        button_frame = tkinter.Frame(self._gui_root)
        button_frame.grid(row=1, column=0, sticky='E', padx=5, pady=5)

        def generate_request_handler(event=None):
            self._on_generate_request()

        def initialize_as_admin_handler(event=None):
            self._on_initialize_as_admin()
            if self._registry.is_initialized():
                self._gui_root.destroy()

        def load_response(event=None):
            self.on_load_response()
            if self._registry.is_initialized():
                self._gui_root.destroy()

        init_admin_button = tkinter.Button(
            button_frame, text='Initialize as Admin',
            command=initialize_as_admin_handler)
        init_admin_button.pack(side=tkinter.LEFT, padx=5)

        generate_button = tkinter.Button(
            button_frame, text='Generate Request',
            command=generate_request_handler)
        generate_button.pack(side=tkinter.RIGHT, padx=5)

        load_resp_button = tkinter.Button(
            button_frame, text='Load Response', command=load_response)
        load_resp_button.pack(side=tkinter.RIGHT, padx=5)

        if self._parent is None:
            self._gui_root.mainloop()

    def _on_generate_request(self):
        '''Handle Generate Request action.'''
        self.log.debug('_on_generate_request called')

        # Ask user for a file location to save the registration request bytes.
        file_path = filedialog.asksaveasfilename(
            parent=self._gui_root,
            title='Save Registration Request',
            initialdir=self._root_dir,
            initialfile='registration.request',
            defaultextension='',
        )
        # If the dialog was cancelled, do nothing
        if not file_path:
            self.log.debug('Save registration request cancelled by user')
            return

        # Retrieve request bytes from registry and write to file
        request_bytes = self._registry.get_request_bytes()

        try:
            with open(file_path, 'wb') as fh:
                fh.write(request_bytes)
        except (OSError, IOError) as e:
            self.log.error('Failed to write registration request to %s: %s', file_path, e)
            try:
                messagebox.showerror('Error', f'Failed to write file: {e}')
            # pylint: disable=bare-except
            except Exception:
                pass
            return

        self.log.info('Registration request saved to %s', file_path)
        messagebox.showinfo('Saved', f'Registration request saved to {file_path}')


    def on_load_response(self):
            '''Handle Load Response button press: apply registration response.'''
            file_path = filedialog.askopenfilename(
                parent=self._gui_root,
                title='Select Registration Response File',
                initialdir=self._root_dir,
                initialfile='registration.response',
                defaultextension='')
            if not file_path:
                return

            try:
                with open(file_path, 'rb') as fh:
                    response_bytes = fh.read()

                # Apply response bytes to registry
                self._registry.set_response_bytes(response_bytes)
                self.log.info('Registration response applied from %s', file_path)

                # Close GUI if registration completed
                if self._registry.is_initialized() and self._gui_root is not None:
                    try:
                        self._gui_root.destroy()
                    # pylint: disable=broad-except
                    except Exception:
                        pass

            except (OSError, IOError) as e:
                self.log.error('Failed to read response file: %s', e)
                messagebox.showerror(
                    'Error',
                    f'Failed to read file: {e}',
                    parent=self._gui_root)
            except (ValueError, KeyError) as e:
                self.log.error('Failed to apply response: %s', e)
                messagebox.showerror(
                    'Error',
                    f'Failed to apply response: {e}',
                    parent=self._gui_root)

    def _on_initialize_as_admin(self):
        ''' Handling initialization as admin '''
        self._registry.initialize_as_admin()

class RegistrationAdmin:
    '''Provides admin-side registration GUI.

    Handles the admin perspective: loading registration requests, assigning roles,
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

        # def on_generate_admin_keys():
        #     '''Stub: Generate admin encryption keys.'''
        #     # TODO: implement admin key generation
        #     self.log.debug('Generate admin keys called')
        #     messagebox.showinfo(
        #         'TODO',
        #         'Admin key generation not yet implemented',
        #         parent=self._admin_window)

        def on_load_request():
            '''Load a registration request file.'''
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

        # gen_keys_btn = tkinter.Button(
        #     section1_frame, text='Generate Admin Keys', command=on_generate_admin_keys)
        # gen_keys_btn.pack(side=tkinter.LEFT, padx=5)

        load_req_btn = tkinter.Button(
            section1_frame, text='Load Registration Request', command=on_load_request)
        load_req_btn.pack(side=tkinter.LEFT, padx=5)

        # ==== SECTION 2: User Data Display ====
        section2_frame = tkinter.LabelFrame(
            self._admin_window, text='User Data (from Request)', padx=10, pady=10)
        section2_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Generate a user data SettingDict from the user config but using
        # default (empty) values.
        self._user_data_dict = SettingDict({
            key: Setting.new(self._user_config.get_setting(key).get_type())
            for key in self._user_config.keys()
            })
        self._user_config.get_setting('email').get_type()

        self._user_data_frame = SettingDictSingleFrame(
            section2_frame,
            setting=self._user_data_dict)
        self._user_data_frame.pack(fill='both', expand=True)

        # ==== SECTION 3: Role Selection ====
        section3_frame = tkinter.LabelFrame(
            self._admin_window, text='Assign Roles', padx=10, pady=10)
        section3_frame.pack(fill='x', padx=10, pady=5)

        # Get available roles from registry
        try:
            available_roles = self._registry.get_roles()
        except (ValueError, KeyError, RuntimeError) as e:
            self.log.error('Failed to get available roles: %s', e)
            available_roles = ['user', 'admin']  # Fallback to default roles

        for role in available_roles:
            var = tkinter.BooleanVar(value=(role == 'user'))  # Default: user role
            checkbox = tkinter.Checkbutton(
                section3_frame,
                text=role.capitalize(),
                variable=var)
            checkbox.pack(anchor='w', padx=10, pady=2)
            self._role_vars[role] = var

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
            selected_roles = [r for r, v in self._role_vars.items() if v.get()]
            if not selected_roles:
                messagebox.showwarning(
                    'No Roles',
                    'Please select at least one role',
                     parent=self._admin_window)
                return

            try:
                # Add user to registry with selected roles
                user_id = self._registry.add_user_from_request(
                    self._current_request, roles=selected_roles)
                self.log.info('User added with ID: %s and roles: %s', user_id, selected_roles)
                messagebox.showinfo(
                    'Success',
                    f'User added successfully!\nUser ID: {user_id}\nRoles: {", ".join(selected_roles)}',
                    parent=self._admin_window)
                self._current_user_id = user_id
            except (ValueError, KeyError) as e:
                self.log.error('Failed to add user: %s', e)
                messagebox.showerror(
                    'Error',
                    f'Failed to add user: {e}',
                    parent=self._admin_window)
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
                response_bytes = self._registry.get_response_bytes(self._current_user_id)

                # Ask user where to save the file
                file_path = filedialog.asksaveasfilename(
                    parent=self._admin_window,
                    title='Save Registration Response',
                    defaultextension='.response',
                    filetypes=[('Response Files', '*.response'), ('All Files', '*.*')],
                    initialfile='registration.response'
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

        close_btn = tkinter.Button(section4_frame, text='Close', command=on_close, width=15)
        close_btn.pack(side=tkinter.LEFT, padx=5)

        add_user_btn = tkinter.Button(
            section4_frame, text='Add User', command=on_add_user, width=15)
        add_user_btn.pack(side=tkinter.LEFT, padx=5)

        write_resp_btn = tkinter.Button(
            section4_frame, text='Write Response', command=on_write_response, width=15)
        write_resp_btn.pack(side=tkinter.LEFT, padx=5)

        if self._parent is None:
            self._admin_window.mainloop()

    def _load_request_ui(self, request_bytes: bytes):
        '''Load and parse registration request, populate UI fields.

        Arguments:
            request_bytes -- Serialized registration request bytes
        '''
        from kiss_cf.registry._registration_request import RegistrationRequest

        try:
            request = RegistrationRequest.from_request(request_bytes)
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
                        self.log.debug('Set %s = %s', key, request.user_data[key])
                    except (ValueError, KeyError) as e:
                        self.log.error('Failed to set %s: %s', key, e)

            # Update individual frames to reflect changed values
            for setting_frame in self._user_data_frame.frame_list:
                setting_frame.update()
        # with newly loaded user data, the user_id is unknown again:
        self._current_user_id = None

        self.log.debug('Request user data: %s', request.user_data)
