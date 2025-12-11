'''Class RegistryGui provides GUI for user registration process.

Manages the initialization of registry (either as admin or as regular user
requesting registration).
'''
import tkinter
import tkinter.ttk

from appxf import logging
from kiss_cf.registry import Registry
from kiss_cf.setting import SettingDict, Setting
from kiss_cf.gui.setting_dict import SettingDictSingleFrame


class RegistryAbortError(Exception):
    '''Used when user aborts the registry process.'''


class Registration:
    '''Provides registry initialization GUI.

    Shows three frames:
    1. Registration Request Data (user data from config)
    2. Admin Public Key (from SettingDict)
    3. Action buttons (Generate Request / Initialize as Admin)
    '''
    log = logging.getLogger(__name__ + '.RegistryGui')

    def __init__(self, registry: Registry, **kwargs):
        super().__init__(**kwargs)
        self._registry = registry

    def check(self):
        '''Check if registry is initialized; if not, show GUI.'''
        if not self._registry.is_initialized():
            self.__run_registry_gui()

    def __run_registry_gui(self):
        '''Show registration GUI with three frames.'''
        guiRoot = tkinter.Tk()
        guiRoot.title('Registry - User Registration')
        guiRoot.rowconfigure(0, weight=1)
        guiRoot.rowconfigure(1, weight=0)
        guiRoot.rowconfigure(2, weight=0)
        guiRoot.columnconfigure(0, weight=1)

        # Frame 1: Registration Request Data (User Data)
        request_frame_label = tkinter.Label(guiRoot, text='Registration Request Data')
        request_frame_label.grid(row=0, column=0, sticky='NW', padx=5, pady=5)

        request_data = SettingDict()
        # Placeholder: in real usage this would come from the registry's user config
        request_frame = SettingDictSingleFrame(guiRoot, setting=request_data)
        request_frame.grid(row=0, column=0, sticky='NSWE', padx=5, pady=5)

        sep1 = tkinter.ttk.Separator(guiRoot, orient='horizontal')
        sep1.grid(row=1, column=0, sticky='WE')

        # Frame 2: Admin Public Key
        admin_key_label = tkinter.Label(guiRoot, text='Admin Public Key')
        admin_key_label.grid(row=2, column=0, sticky='NW', padx=5, pady=5)

        admin_key_text = tkinter.Text(guiRoot, width=60, height=5)
        admin_key_text.grid(row=2, column=0, sticky='NSWE', padx=5, pady=5)
        # Placeholder: in real usage this would read from SettingDict
        admin_key_text.insert('1.0', '(Admin public key would appear here)')

        sep2 = tkinter.ttk.Separator(guiRoot, orient='horizontal')
        sep2.grid(row=3, column=0, sticky='WE')

        # Frame 3: Action Buttons
        button_frame = tkinter.Frame(guiRoot)
        button_frame.grid(row=4, column=0, sticky='E', padx=5, pady=5)

        def generate_request_handler(event=None):
            '''Handle Generate Request button press.'''
            self.log.debug('Generate Request button pressed')
            guiRoot.destroy()
            self.__on_generate_request()

        def initialize_as_admin_handler(event=None):
            '''Handle Initialize as Admin button press.'''
            self.log.debug('Initialize as Admin button pressed')
            guiRoot.destroy()
            self.__on_initialize_as_admin()

        init_admin_button = tkinter.Button(
            button_frame, text='Initialize as Admin',
            command=initialize_as_admin_handler)
        init_admin_button.pack(side=tkinter.LEFT, padx=5)

        generate_button = tkinter.Button(
            button_frame, text='Generate Request',
            command=generate_request_handler)
        generate_button.pack(side=tkinter.RIGHT, padx=5)

        guiRoot.mainloop()

        if not self._registry.is_initialized():
            raise RegistryAbortError

    def __on_generate_request(self):
        '''Handle Generate Request action (placeholder).'''
        self.log.debug('__on_generate_request called')
        # TODO: Implement generate request logic

    def __on_initialize_as_admin(self):
        '''Handle Initialize as Admin action (placeholder).'''
        self.log.debug('__on_initialize_as_admin called')
        # TODO: Implement initialize as admin logic

    def register_user(self):
        ''' pop up toplevel window for user registration

        Arguments:
            security -- Security object to retrieve encryption key from.
                       If None, no key is displayed.
        '''
        self.log.debug('register_user called')

        # Create TopLevel window
        toplevel = tkinter.Toplevel()
        toplevel.title('User Registration - Encryption Key')
        toplevel.geometry('600x400')

        # Main label
        main_label = tkinter.Label(
            toplevel,
            text='User Encryption Key',
            font=('TkDefaultFont', 12, 'bold'))
        main_label.pack(padx=10, pady=10)

        # Get user's encryption key
        encryption_key = self._registry.get_encryption_key()


        # Create SettingDict with encryption key for display
        encryption_key_setting = Setting.new('base64',
            value=encryption_key,
            name='Encryption Key')

        settings_dict = SettingDict({
            'Encryption Key': encryption_key_setting,
            })

        # Display settings using SettingDictSingleFrame
        frame = SettingDictSingleFrame(toplevel, setting=settings_dict)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Close button
        close_button = tkinter.Button(
            toplevel,
            text='Close',
            command=toplevel.destroy)
        close_button.pack(pady=10)
