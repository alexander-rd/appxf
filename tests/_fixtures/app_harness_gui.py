''' Provide a GUI for the application harness '''
from kiss_cf.gui import KissApplication
from tests._fixtures.app_harness import AppHarness

class AppHarnessGui():
    def __init__(self, harness: AppHarness):
        self.harness = harness
        self.kiss_app = KissApplication()
