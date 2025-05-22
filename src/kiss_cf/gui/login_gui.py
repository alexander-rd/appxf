'''Class Login provides GUI to init user data and get password.

Exception UserAbortError is defined to terminate the application on
Login.check().
'''
import tkinter
import tkinter.ttk

from appxf import logging
# from kiss_cf.config import Config
from kiss_cf.setting import SettingDict
from kiss_cf.gui.setting_dict import SettingDictSingleFrame
from kiss_cf.security import Security


class UserAbortError(Exception):
    '''Used when user aborts the login process.'''


# TODO: The login should be more general of also collecting USER info. It makes
# sense that login initialization collects extra data. And it makes sense that
# this data in configuration. But:
#  * The config section should be an option
#  * If no config section is provided (or no option is present), the curser
#    should start with focus on password.
# Best would be to become independent of configuration. But: YAGNI.

class Login():
    '''Provides login process including initialization of user data.

    Main aim of having a login procedure is to protect locally stored data by a
    password. Secondary is collecting user information on first usage of a
    tool. Therefore, a configuration object defining expected user data is the
    main input.

    Output of the login procedure is a configuration object with the stored
    user data and the following added to it:
     * key: a secred key that is used to encrypt locally stored data
    '''
    log = logging.getLogger(__name__ + '.Login')

    def __init__(self, security: Security,
                 user_config: SettingDict=SettingDict(),
                 app_name='Login',
                 pwd_min_length=6,
                 **kwargs):
        super().__init__(**kwargs)
        self._security = security
        self._user_config = user_config
        self._app_name = app_name
        self._pwd_min_length = pwd_min_length

    def check(self):
        if not self._security.is_user_initialized():
            self.__run_init_gui()
        # TODO: we also have to check if the source file for USER is present.
        # This would also indicate not being initialized.

        if not self._security.is_user_unlocked():
            self.__run_login_gui()

    def __run_init_gui(self):
        '''Get USER configuration and initial password.

        After verifying the password (length, repetition matches), a key is
        derived from it. Only this derived key is returned. The password itself
        is not stored.
        '''
        guiRoot = tkinter.Tk()
        guiRoot.title(self._app_name)
        guiRoot.rowconfigure(0, weight=1)
        guiRoot.columnconfigure(1, weight=1)

        userConfig = SettingDictSingleFrame(guiRoot, setting=self._user_config)
        userConfig.grid(row=0, column=0, sticky='NSWE', columnspan=2)
        left_min_size_config = userConfig.get_left_col_min_width()

        sep = tkinter.ttk.Separator(guiRoot, orient='horizontal')
        sep.grid(row=1, column=0, columnspan=2, sticky='WE')

        pwdLabel = tkinter.Label(guiRoot, justify='right')
        pwdLabel.config(text='Passwort:')
        pwdLabel.grid(row=2, column=0, padx=5, pady=5, sticky='E')

        pwdRepLabel = tkinter.Label(guiRoot, justify='right')
        pwdRepLabel.config(text='Passwort wiederholen:')
        pwdRepLabel.grid(row=3, column=0, padx=5, pady=5, sticky='E')

        pwdEntry = tkinter.Entry(guiRoot, show="*", width=20)
        pwdEntry.grid(row=2, column=1, padx=5, pady=5, sticky='W')

        pwdRepEntry = tkinter.Entry(guiRoot, show="*", width=20)
        pwdRepEntry.grid(row=3, column=1, padx=5, pady=5, sticky='W')

        # get password left column min width
        guiRoot.update()
        left_min_size_login = max(
            [pwdLabel.winfo_width(), pwdRepLabel.winfo_width()]
            ) + 10
        left_min_size = max([left_min_size_config, left_min_size_login])
        # adjust column here and in config
        userConfig.set_left_column_min_width(left_min_size)
        guiRoot.columnconfigure(0, minsize=left_min_size)

        # TODO: when leaving one pwd entry and both do not match, color the
        # repetition red

        def okButtonFunction(event=None):
            valid = True
            pwdEntry   .config(foreground='black')
            pwdRepEntry.config(foreground='black')

            if (len(pwdEntry.get()) < self._pwd_min_length):
                self.log.debug('NOK, Passwort muss mindestens '
                               f'{self._pwd_min_length} Zeichen haben')
                pwdEntry   .config(foreground='red')
                valid = False
            if (pwdEntry.get() != pwdRepEntry.get()):
                self.log.debug('NOK, Passwords do not match')
                pwdRepEntry.config(foreground='red')
                valid = False
            if not userConfig.is_valid():
                self.log.debug('config not valid')
                valid = False
            if valid:
                # unlock user
                self._security.init_user(pwdEntry.get())
                # store USER configuration
                self._user_config.store()
                self.log.debug('OK, quit')
                guiRoot.destroy()
        okButton = tkinter.Button(guiRoot, text='OK', command=okButtonFunction)
        okButton.grid(row=4, column=1, padx=5, pady=5, sticky='E')

        guiRoot.bind('<Return>', okButtonFunction)
        guiRoot.bind('<KP_Enter>', okButtonFunction)
        userConfig.focus_curser_on_first_entry()
        guiRoot.mainloop()

        if not self._security.is_user_initialized():
            raise UserAbortError

    def __run_login_gui(self):
        guiRoot = tkinter.Tk()
        guiRoot.title(self._app_name)
        guiRoot.rowconfigure(1, weight=1)
        guiRoot.columnconfigure(1, weight=1)
        guiRoot.columnconfigure(2, weight=1)

        pwdLabel = tkinter.Label(guiRoot, justify='right')
        pwdLabel.config(text='Passwort:')
        pwdLabel.grid(row=2, column=1, padx=5, pady=5, sticky='E')

        pwdEntry = tkinter.Entry(guiRoot, show="*", width=20)
        pwdEntry.grid(row=2, column=2, padx=5, pady=5, sticky='W')

        def okButtonFunction(event=None):
            try:
                self._security.unlock_user(pwdEntry.get())
                # self._config.load('USER')
                guiRoot.destroy()
            except Exception:
                self.log.debug('Password verification failed because of:',
                               exc_info=True)
                self.log.warning('Password wrong, but we continue.')

        okButton = tkinter.Button(guiRoot, text="OK", command=okButtonFunction)
        okButton.grid(row=3, column=2, padx=5, pady=5, sticky='E')

        guiRoot.bind('<Return>', okButtonFunction)
        guiRoot.bind('<KP_Enter>', okButtonFunction)
        pwdEntry.focus_set()
        guiRoot.mainloop()

        # TODO: check missing for loaded configuration
        # config.is_section_loaded()
        if not self._security.is_user_unlocked():
            raise UserAbortError
