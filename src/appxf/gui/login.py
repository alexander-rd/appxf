# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
"""Class Login provides GUI to init user data and get password.

Exception UserAbortError is defined to terminate the application on
Login.check().
"""

import tkinter
import tkinter.ttk

from appxf import logging
from appxf.gui.locale import _
from appxf.gui.setting_dict import SettingDictSingleFrame
from appxf.security import Security

# from appxf.config import Config
from appxf.setting import SettingDict


class UserAbortError(Exception):
    """Used when user aborts the login process."""


# TODO: The login should be more general of also collecting USER info. It makes
# sense that login initialization collects extra data. And it makes sense that
# this data in configuration. But:
#  * The config section should be an option
#  * If no config section is provided (or no option is present), the curser
#    should start with focus on password.
# Best would be to become independent of configuration. But: YAGNI.


class Login:
    """Provides login process including initialization of user data.

    Main aim of having a login procedure is to protect locally stored data by a
    password. Secondary is collecting user information on first usage of a
    tool. Therefore, a configuration object defining expected user data is the
    main input.

    Output of the login procedure is a configuration object with the stored
    user data and the following added to it:
     * key: a secred key that is used to encrypt locally stored data
    """

    log = logging.get_logger(__name__ + ".Login")

    def __init__(
        self,
        security: Security,
        user_config: SettingDict | None = None,
        app_name="Login",
        pwd_min_length=6,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._security = security
        if user_config is None:
            self._user_config = SettingDict()
        else:
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
        """Get USER configuration and initial password.

        After verifying the password (length, repetition matches), a key is
        derived from it. Only this derived key is returned. The password itself
        is not stored.
        """
        gui_root = tkinter.Tk()
        gui_root.title(_("window", "Login - Initialize"))
        gui_root.rowconfigure(0, weight=1)
        gui_root.columnconfigure(1, weight=1)

        user_config = SettingDictSingleFrame(
            gui_root, setting=self._user_config, frame_label=False
        )
        user_config.grid(row=0, column=0, sticky="NSWE", columnspan=2)
        left_min_size_config = user_config.get_left_col_min_width()

        sep = tkinter.ttk.Separator(gui_root, orient="horizontal")
        sep.grid(row=1, column=0, columnspan=2, sticky="WE")

        pwd_label = tkinter.Label(gui_root, justify="right")
        pwd_label.config(text=_("label", "Password:"))
        pwd_label.grid(row=2, column=0, padx=5, pady=5, sticky="E")

        pwd_rep_label = tkinter.Label(gui_root, justify="right")
        pwd_rep_label.config(text=_("label", "Repeat Password:"))
        pwd_rep_label.grid(row=3, column=0, padx=5, pady=5, sticky="E")

        pwd_entry = tkinter.Entry(gui_root, show="*", width=20)
        pwd_entry.grid(row=2, column=1, padx=5, pady=5, sticky="W")

        pwd_rep_entry = tkinter.Entry(gui_root, show="*", width=20)
        pwd_rep_entry.grid(row=3, column=1, padx=5, pady=5, sticky="W")

        # get password left column min width
        gui_root.update()
        left_min_size_login = (
            max([pwd_label.winfo_width(), pwd_rep_label.winfo_width()]) + 10
        )
        left_min_size = max([left_min_size_config, left_min_size_login])
        # adjust column here and in config
        user_config.set_left_column_min_width(left_min_size)
        gui_root.columnconfigure(0, minsize=left_min_size)

        # TODO: when leaving one pwd entry and both do not match, color the
        # repetition red

        def ok_button_function(event=None):
            valid = True
            pwd_entry.config(foreground="black")
            pwd_rep_entry.config(foreground="black")

            if len(pwd_entry.get()) < self._pwd_min_length:
                self.log.debug(
                    "NOK, Passwort muss mindestens "
                    f"{self._pwd_min_length} Zeichen haben"
                )
                pwd_entry.config(foreground="red")
                valid = False
            if pwd_entry.get() != pwd_rep_entry.get():
                self.log.debug("NOK, Passwords do not match")
                pwd_rep_entry.config(foreground="red")
                valid = False
            if not user_config.is_valid():
                self.log.debug("config not valid")
                valid = False
            if valid:
                # unlock user
                self._security.init_user(pwd_entry.get())
                # store USER configuration
                self._user_config.store()
                self.log.debug("OK, quit")
                gui_root.destroy()

        ok_button = tkinter.Button(
            gui_root, text=_("button", "OK"), command=ok_button_function
        )
        ok_button.grid(row=4, column=1, padx=5, pady=5, sticky="E")

        gui_root.bind("<Return>", ok_button_function)
        gui_root.bind("<KP_Enter>", ok_button_function)
        user_config.focus_curser_on_first_entry()
        gui_root.mainloop()

        if not self._security.is_user_initialized():
            raise UserAbortError

    def __run_login_gui(self):
        gui_root = tkinter.Tk()
        gui_root.title(_("window", "Login"))
        gui_root.rowconfigure(1, weight=1)
        gui_root.columnconfigure(1, weight=1)
        gui_root.columnconfigure(2, weight=1)

        pwd_label = tkinter.Label(gui_root, justify="right")
        pwd_label.config(text=_("label", "Password:"))
        pwd_label.grid(row=2, column=1, padx=5, pady=5, sticky="E")

        pwd_entry = tkinter.Entry(gui_root, show="*", width=20)
        pwd_entry.grid(row=2, column=2, padx=5, pady=5, sticky="W")

        def ok_button_function(event=None):
            try:
                self._security.unlock_user(pwd_entry.get())
                gui_root.destroy()
            except Exception:
                self.log.debug(
                    "Password verification failed because of:", exc_info=True
                )
                self.log.warning("Password wrong, but we continue.")

        ok_button = tkinter.Button(
            gui_root, text=_("button", "OK"), command=ok_button_function
        )
        ok_button.grid(row=3, column=2, padx=5, pady=5, sticky="E")

        gui_root.bind("<Return>", ok_button_function)
        gui_root.bind("<KP_Enter>", ok_button_function)
        pwd_entry.focus_set()
        gui_root.mainloop()

        # TODO: check missing for loaded configuration
        # config.is_section_loaded()
        if not self._security.is_user_unlocked():
            raise UserAbortError
