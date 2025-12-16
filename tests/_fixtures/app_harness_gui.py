''' Provide a GUI for the application harness '''
from kiss_cf.gui import KissApplication, ConfigMenu, Login
from kiss_cf.gui import RegistrationUser, RegistrationAdmin
from tests._fixtures.app_harness import AppHarness
import tkinter


class AppHarnessGui():
    def __init__(
        self,
        harness: AppHarness,
        *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.harness = harness
        self.app_name = f'AppHarnessGui for {harness.user}'

    def _run_application(self):
        app = KissApplication()
        # === Main Window === #
        app.geometry('600x200')
        app.title(self.app_name)

        # --- Frames --- #
        # There could be frames added via self.kiss_app.register_frame but the
        # application for testing does not have any behavior.

        # TODO: The frame switching provided by KissApplication() should have a
        # manual test where frames should be added. Optional: from the frames,
        # it should be possible to access other features that are typically
        # within the menus.

        # --- Config Menu --- #
        configMenu = ConfigMenu(app, self.harness.config)
        # gui_root.frame_menu.add_separator()
        app.frame_menu.add_cascade(label='Config', menu=configMenu)

        # --- Registration Menu --- #
        if (self.harness.registry_enabled and
            self.harness.registry.is_initialized() and
            'admin' in self.harness.registry.get_roles(user_id=0)
            ):
            def show_registration():
                registration = RegistrationAdmin(
                    registry=self.harness.registry,
                    root_dir=self.harness.root_path,
                    user_config=self.harness.config.section('USER'))
                registration.show()
            app.frame_menu.add_command(
                label='Registration',
                command=show_registration)




        app.mainloop()

    def start(self) -> None:
        # Chek login state before application start
        if self.harness.login_enabled and not self.harness.security.is_user_unlocked():
            login = Login(
                security=self.harness.security,
                user_config=self.harness.config.section('USER'),
                app_name='Login: ' + self.app_name)
            login.check()

        # config is privately encrypted and must be loaded before any sync
        # (even if sync may update it):
        self.harness.config.load()

        # ensure registry being initialized
        if self.harness.registry_enabled and not self.harness.registry.is_initialized():
            registration = RegistrationUser(
                registry = self.harness.registry,
                root_dir = self.harness.root_path)
            if not registration.check():
                return

        # loading regitry will happen automatically when required - like during
        # a sync attempt:
        #
        # TODO: the sync attempt

        self._run_application()
