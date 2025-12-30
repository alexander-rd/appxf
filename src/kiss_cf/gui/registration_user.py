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

# TODO: This file is in DRAFT STATUS, mostly generated with GitHub copilot and
# needs a detailed review. Currently, getting the GUI and behavior right is
# prioritized since it may considerably impact this implementation.


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
        # request_frame_label = tkinter.Label(
        #     self._gui_root, text='Registration Request Data')
        # request_frame_label.grid(
        #     row=0, column=0, sticky='NW', padx=5, pady=5)

        # request_data = SettingDict()
        # Placeholder: in real usage this would come from the registry's
        # user config
        # request_frame = SettingDictSingleFrame(
        #     self._gui_root, setting=request_data)
        # request_frame.grid(row=0, column=0, sticky='NSWE', padx=5, pady=5)

        # sep1 = tkinter.ttk.Separator(self._gui_root, orient='horizontal')
        # sep1.grid(row=1, column=0, sticky='WE')

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
            self.log.error(
                'Failed to write registration request to %s: %s',
                file_path,
                e,
            )
            try:
                messagebox.showerror(
                    'Error', f'Failed to write file: {e}'
                )
            except Exception:  # pylint: disable=bare-except
                pass
            return

        self.log.info('Registration request saved to %s', file_path)
        messagebox.showinfo(
            'Saved', f'Registration request saved to {file_path}'
        )

    def on_load_response(self):
        '''Handle Load Response button press:
        apply registration response.'''
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
            self.log.info(
                'Registration response applied from %s', file_path
            )

            # Close GUI if registration completed
            if (
                self._registry.is_initialized()
                and self._gui_root is not None
            ):
                try:
                    self._gui_root.destroy()
                except Exception:  # pylint: disable=broad-except
                    pass

        except (OSError, IOError) as e:
            self.log.error('Failed to read response file: %s', e)
            messagebox.showerror(
                'Error',
                f'Failed to read file: {e}',
                parent=self._gui_root,
            )
        except (ValueError, KeyError) as e:
            self.log.error('Failed to apply response: %s', e)
            messagebox.showerror(
                'Error',
                f'Failed to apply response: {e}',
                parent=self._gui_root,
            )

    def _on_initialize_as_admin(self):
        ''' Handling initialization as admin '''
        self._registry.initialize_as_admin()
