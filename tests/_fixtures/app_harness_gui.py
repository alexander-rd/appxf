''' Provide a GUI for the application harness '''
from kiss_cf.gui import KissApplication, ConfigMenu, Login, Registration
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
        if self.harness.registry_enabled and self.harness.registry.is_initialized():
            registration = Registration(registry=self.harness.registry)
            app.frame_menu.add_command(
                label='Registration',
                command=lambda: registration.register_user())

        # Problem: the base64 encoded encryption key has this length, the line
        # length is from what a reasonably sized pop-up window can display.
        # Those are 55 characters per line, 392 characters. Those are 294 bytes
        # (due to DER encoding). The key is 2048 bit and 256 bytes such that
        # there is no significant gain.
        #
        # MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuS0eHWUOg2N
        # DM8w7wsYF4/cJl/dpoB+Ru3zVVr77joFpojfNmFzwXnQnOyWwUgoX4k
        # kFjELXzOO9FZ7i830ua6y0jvZqaU1Cvlamtvs1slH+62pDKHFDnTifo
        # 7O9goFSmHHLi2GJ8aoRgEfb/4wJVdN8B6iA8bctWKxduEBZiCfF03rI
        # EyHJaRjsqLZpYBC7jri6OCWlxU+8kEZyvpSgwyB2hwfGE1lG5K8MR/R
        # LA7ANi0YUcZ4VqGSQGyYM0LalupX4w2UXJjxBT17UblTUa/+HEKHsvx
        # DyO5CDtbYUZkjwXXgoJ3jt76gcazoFYikG+VjhK0V8cU5vfVWYU6lB8
        # wIDAQAB------------------------------------------------
        #
        # Conlcusion: key should also be exchanged by a file. If it will be per
        # file, we can as well send ALL admin keys.

        # --- Adding more menu items --- #
        #topMenu = tkinter.Menu(self)
        #self.config(menu=topMenu)
        #topMenu.add_command(label="Item A", command=lambda: print('Menu: item A'))
        #topMenu.add_command(label="Item B", command=lambda: print('Menu: item B'))
        # self.update()

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
            registration = Registration(
                registry = self.harness.registry)
            registration.check()

        # loading regitry will happen automatically when required - like during
        # a sync attempt:
        #
        # TODO: the sync attempt

        self._run_application()
