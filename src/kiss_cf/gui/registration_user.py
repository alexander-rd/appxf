''' Providing GUI classes for user registration

- RegistrationUser is the user perspective for generating registration requests
  and loading responses (or initializing as admin).
- RegistrationAdmin is the admin perspective for reviewing requests, assigning
  roles, and generating responses.
'''
import tkinter
from tkinter import filedialog, messagebox

from appxf import logging
from kiss_cf.registry import Registry
from kiss_cf.gui.common import GridFrame, GridTk, GridToplevel
from kiss_cf.gui.common import ButtonFrame
from kiss_cf.gui.locale import _

# TODO: This file is in DRAFT STATUS, mostly generated with GitHub copilot and
# needs a detailed review. Currently, getting the GUI and behavior right is
# prioritized since it may considerably impact this implementation.

log = logging.getLogger(__name__)

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
                 hide_admin_keys: bool = False,
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
        self._gui_root: GridTk | GridToplevel | None = None
        self._registration_buttons: ButtonFrame | None = None
        self._hide_admin_keys = hide_admin_keys

        if self._hide_admin_keys and not self._registry.has_admin_keys:
            raise ValueError(
                'hide_admin_keys is True but registry has no admin keys loaded. '
                'Make sure you load admin keys before calling user registration '
                'when hiding the admin keys section.')

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
        '''Build user registration GUI'''
        # Create root window (Tk) or toplevel (Toplevel) depending on parent
        if self._parent is None:
            self._gui_root = GridTk(
                title=_('window', 'Registry - User Registration'),
                buttons=[])
        else:
            self._gui_root = GridToplevel(
                self._parent,
                title=_('window', 'User Registration'),
                buttons = [])
        if self._gui_root.frame is None:
            raise RuntimeError('This should not happen')

        # Define translated button labels for consistent referencing
        self._button_load_admin_keys = _('button', 'Load Admin Keys')
        self._button_initialize_as_admin = _('button', 'Initialize as Admin')
        self._button_write_request = _('button', 'Write Request')
        self._button_load_response = _('button', 'Load Response')

        current_row = 0
        if not self._hide_admin_keys:
            admin_frame = GridFrame(self._gui_root, text=_('label', 'Admin Keys'))
            self._gui_root.frame.place(admin_frame, row=0, column=0)
            current_row += 1

            # Button row for Admin Keys
            admin_buttons = ButtonFrame(admin_frame, buttons=[self._button_load_admin_keys, self._button_initialize_as_admin, ''])
            admin_frame.place(widget=admin_buttons, row=0, column=0)

            # Status text (unlabeled) to display admin status
            self._admin_status_var = tkinter.StringVar(value='')
            admin_status_label = tkinter.Label(admin_frame, textvariable=self._admin_status_var, anchor='w')
            admin_frame.place(widget=admin_status_label, row=1, column=0)

            # Hook up events from button frames to wrapper methods that update status
            admin_buttons.bind(f'<<{self._button_load_admin_keys}>>', lambda event: self._on_load_admin_keys())
            admin_buttons.bind(f'<<{self._button_initialize_as_admin}>>', lambda event: self._on_initialize_as_admin())

        # Registration frame (row 1)
        registration_frame = GridFrame(self._gui_root, text=_('label', 'Registration'))
        self._gui_root.frame.place(registration_frame, row=current_row, column=0)
        current_row += 1

        # Buttons for registration: Write Request and Load Response
        self._registration_buttons = ButtonFrame(registration_frame, buttons=[self._button_write_request, self._button_load_response, ''])
        registration_frame.place(widget=self._registration_buttons, row=0, column=0)

        self._registration_buttons.bind(f'<<{self._button_write_request}>>', lambda event: self._on_generate_request())
        self._registration_buttons.bind(f'<<{self._button_load_response}>>', lambda event: self._on_load_response())

        # call status updater at init
        self._update_admin_status()

    def _update_admin_status(self):
        '''Update admin status text. Dummy implementation for now.'''
        if self._registration_buttons is None:
            return

        if self._registry.has_admin_keys():
            status = _('status', 'Admin keys are already loaded to encrypt your user data.')
            self._registration_buttons.set_button_active(self._button_write_request, True)
            self._registration_buttons.set_button_active(self._button_load_response, True)
        else:
            status = _('status', 'You have to load admin keys to encrypt the user data in your request.')
            self._registration_buttons.set_button_active(self._button_write_request, False)
            self._registration_buttons.set_button_active(self._button_load_response, False)
        if not self._hide_admin_keys:
            self._admin_status_var.set(status)

    def _check_init_status(self):
        if (
                self._registry.is_initialized()
                and self._gui_root is not None
            ):
            self._gui_root.destroy()

    def _on_generate_request(self):
        '''Handle Generate/Write Request action.'''
        self.log.debug('_on_generate_request called')

        # Ask user for a file location to save the registration request bytes.
        file_path = filedialog.asksaveasfilename(
            parent=self._gui_root,
            title=_('dialog', 'Save Registration Request'),
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
            self.log.error(
                'Failed to write registration request to %s: %s',
                file_path,
                e,
            )
            messagebox.showerror(
                'Error', _('error', 'Failed to write file: {}').format(e),
                parent=self._gui_root,
            )
            return

        self.log.info('Registration request saved to %s', file_path)

    def _on_load_response(self):
        '''Handle Load Response button press:
        apply registration response.'''
        file_path = filedialog.askopenfilename(
            parent=self._gui_root,
            title=_('dialog', 'Select Registration Response File'),
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
            self.log.info(
                'Registration response applied from %s', file_path
            )

            # Close GUI if registration completed
            self._check_init_status()

        except (OSError, IOError) as e:
            self.log.error('Failed to read response file: %s', e)
            messagebox.showerror(
                'Error',
                _('error', 'Failed to read file: {}').format(e),
                parent=self._gui_root,
            )
        except (ValueError, KeyError) as e:
            self.log.error('Failed to apply response: %s', e)
            messagebox.showerror(
                'Error',
                _('error', 'Failed to apply response: {}').format(e),
                parent=self._gui_root,
            )

    def _on_initialize_as_admin(self):
        ''' Handling initialization as admin '''
        self._registry.initialize_as_admin()
        self._check_init_status()

    def _on_load_admin_keys(self):
        '''Load admin key bytes from file and apply to registry.'''
        file_path = filedialog.askopenfilename(
            parent=self._gui_root,
            title=_('dialog', 'Select Admin Keys File'),
            initialdir=self._root_dir,
            initialfile='admin.keys',
            defaultextension='')
        if not file_path:
            return
        try:
            with open(file_path, 'rb') as fh:
                key_bytes = fh.read()
            self._registry.set_admin_key_bytes(key_bytes)
            self._update_admin_status()
            self._check_init_status()
        except Exception as e:
            self.log.error('Failed to load admin keys: %s', e)
            try:
                messagebox.showerror('Error', _('error', 'Failed to load admin keys: {}').format(e), parent=self._gui_root)
            except Exception:
                pass
            return
        self.log.info('Admin keys loaded from %s', file_path)

