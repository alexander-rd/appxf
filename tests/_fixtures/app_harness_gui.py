''' Provide a GUI for the application harness '''
from kiss_cf.gui import KissApplication, ConfigMenu, Login
from tests._fixtures.app_harness import AppHarness
import tkinter


class AppHarnessGui():
    def __init__(
        self,
        harness: AppHarness,
        login_enabled: bool = True,
        registry_enabled: bool = False,
        *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.harness = harness
        self.app_name = f'AppHarnessGui for {harness.user}'
        self.login_enabled = login_enabled
        self.registry_enabled = registry_enabled

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
        configMenu = ConfigMenu(app, self.harness.user_config)
        # gui_root.frame_menu.add_separator()
        app.frame_menu.add_cascade(label='Config', menu=configMenu)

        # --- Adding more menu items --- #
        #topMenu = tkinter.Menu(self)
        #self.config(menu=topMenu)
        #topMenu.add_command(label="Item A", command=lambda: print('Menu: item A'))
        #topMenu.add_command(label="Item B", command=lambda: print('Menu: item B'))
        # self.update()
        app.mainloop()

    def start(self) -> None:
        # Chek login state before application start
        if self.login_enabled and not self.harness.security.is_user_unlocked():
            login = Login(
                security=self.harness.security,
                user_config=self.harness.user_config.section('USER'),
                app_name='Login: ' + self.app_name)
            login.check()

        self._run_application()
