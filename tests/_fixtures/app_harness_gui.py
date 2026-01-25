''' Provide a GUI for the application harness '''
import os
from kiss_cf.gui import KissApplication, ConfigMenu, Login
from kiss_cf.gui import RegistrationUser, RegistrationAdmin
from tests._fixtures.app_harness import AppHarness


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
        configMenu = ConfigMenu(
            parent=app,
            config=self.harness.config,
            registry=self.harness.registry,
            root_path=self.harness.root_path)
        # gui_root.frame_menu.add_separator()
        app.frame_menu.add_cascade(label='Config', menu=configMenu)

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

        # ensure registry being initialized while including a hidden feature:
        # not showing admin keys section if admin keys are available:
        if self.harness.registry_enabled and not self.harness.registry.is_initialized():
            admin_keys_path = os.path.join(self.harness.app_path, 'admin.keys')
            hide_admin_keys = False
            if os.path.exists(admin_keys_path):
                if not self.harness.registry.has_admin_keys():
                    with open(admin_keys_path, 'rb') as f:
                        admin_keys_data = f.read()
                        self.harness.registry.set_admin_key_bytes(
                            admin_keys_data)
                hide_admin_keys = True
            registration = RegistrationUser(
                registry = self.harness.registry,
                root_dir = self.harness.root_path,
                hide_admin_keys=hide_admin_keys)
            if not registration.check():
                return

        # loading regitry will happen automatically when required - like during
        # a sync attempt:
        #
        # TODO: the sync attempt

        self._run_application()
