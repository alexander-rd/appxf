''' Monkey-Patching tkinter to allow automated tests behind a Tk()

General problem: tox does not support any graphics and, therefore, cannot
initialize a Tk() application even if you don't start the Tk.mainloop().

This module provides fake classes for tkinter, but they must be activated
before tkinter is used (imported) anywhere else.

```
from tests import fake_tkinter
fake_tkinter.activate()
# your other stuff
import my_module_with_tkinter
```
'''
import tkinter

def dummy_function(*args, **kwargs):
    pass

# Monkey-Patching Tk(). We need this to run those automated tests in tox:
class FakeTk(object):
    def __init__(self):
        print('Tk() init called')

    rowconfigure = dummy_function
    columnconfigure = dummy_function
    config = dummy_function

    def mainloop(self):
        raise Exception('This automated test should NOT start the GUI')


# When other functions access other base classes, those also need to get
# monkey-patched since they would call back to parents.
class FakeFrame(object):
    def __init__(self, *args, **kwargs):
        print('Frame() init called')

    grid = dummy_function
    tkraise = dummy_function


class FakeMenu(object):
    def __init__(self, *args, **kwargs):
        print('Menu() init called')

    add_cascade = dummy_function
    add_command = dummy_function


def activate():
    tkinter.__dict__['Tk'] = FakeTk
    tkinter.__dict__['Frame'] = FakeFrame
    tkinter.__dict__['Menu'] = FakeMenu
