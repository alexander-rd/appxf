''' Provide a GUI for the application harness '''
from kiss_cf.gui import KissApplication, ConfigMenu
from tests._fixtures.app_harness import AppHarness
import tkinter


class AppHarnessGui(KissApplication):
    def __init__(self, harness: AppHarness, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.harness = harness

        # === Main Window === #
        self.geometry('600x200')
        self.title(f'AppHarnessGui for {harness.user}')

        # --- Frames --- #
        # There could be frames added via self.kiss_app.register_frame but the
        # application for testing does not have any behavior.

        # TODO: The frame switching provided by KissApplication() should have a
        # manual test where frames should be added. Optional: from the frames,
        # it should be possible to access other features that are typically
        # within the menus.

        # --- Config Menu --- #
        configMenu = ConfigMenu(self, harness.user_config)
        # gui_root.frame_menu.add_separator()
        self.frame_menu.add_cascade(label='Config', menu=configMenu)

        # --- Adding more menu items --- #
        #topMenu = tkinter.Menu(self)
        #self.config(menu=topMenu)
        #topMenu.add_command(label="Item A", command=lambda: print('Menu: item A'))
        #topMenu.add_command(label="Item B", command=lambda: print('Menu: item B'))
        # self.update()