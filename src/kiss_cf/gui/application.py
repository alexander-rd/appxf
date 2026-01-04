

# Note on decision: switching main frame
#
# Switching frames in the web is done by constructing all necessary views and
# then pulling the one of current interest to the front.
#  - (+) you can switch between views and the state of the view remains like
#    you left it.
#  - (/) the above supports to link elements of one frame with one from another
#    view. But does not support isolating use cases (frames) from each other.
#  - (-) If constructing views has side effects (loading time, gathering data
#    from a database), this will happen at startup, even if the frame is never
#    used.
#
# An alternative is to switch frames by properly destroying the old one and
# constructing the new one to display.
#  - (-) This is more complicated to do and might not be recommended given the
#    web research. By that base: it is not exactly KISS.
#  - (-) It is not possible to link behavior of different views.
#  - (/) Since the frame is destroyed, opening it again will show a fresh
#    state. This can be intended or not.
#
# A compromise would be to construct a frame when needed but then, retaining
# it. This alternative should be well compatible with constructing all frames
# from the beginning but more co plex to implement.
#
# Conclusion: We should go with the first alternative but keep the interface
# compatible to the compromise. This will imply that KissApplication does not
# take a contructed Frame, only the required class.

import tkinter
from recordclass import RecordClass


class FrameInfo(RecordClass):
    cls: type[tkinter.Frame]
    args: tuple
    kwargs: dict
    frame: None | tkinter.Frame


class KissApplication(tkinter.Tk):
    ''' Main Application Window

    This Application Window includes:
      * a top level menu bar [.menu] with
        * options to switch between frames [.menu TODO]
        * possibility to add more menu items [.TODO]
      * main frame which can show whatever frame you registered:
        [.register_frame()] and [.show_frame()]
      * a lower logging display [TODO]
      * handle login, registry and sync if defined [TODO]

    Typical code would look like

    ``` from your_app import WelcomeFrame, ViewOneFrame from kiss_cf.appframe
    import ApplicationFrame

    af = ApplicationFrame()
    af.register_frame('welcome', WelcomeFrame)
    af.register_frame('one', ViewOneFrame)
    af.show_frame('welcome')
    # if required, af.main_frame could be manipulated
    af.mainloop()
    ```
    '''

    def __init__(self, *args, **kwargs):
        ''' Create Kiss Application Window

        Arguments: just forwarding args/kwargs to tkinter.Tk
        '''
        super().__init__(*args, **kwargs)
        self._frames: dict[str, FrameInfo] = dict()
        self._dummy_frame = FrameInfo(tkinter.Frame, (), {}, None)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # ensure the dummy frame is existent
        self.show_frame('')

        # bring menu to life:
        self.menu = tkinter.Menu(self)
        self.frame_menu = tkinter.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label='View', menu=self.frame_menu)
        # TODO: We can have (1) no menu at all, (2) a cascaded menu which needs
        # a name for the cascade or (3) the frame names directly within the top
        # bar.
        #
        # For now, we use only (3).
        #
        # When switching to allow (1) and (2), it must be clear how to extend
        # the menu. In case of (2): the user will likely extend the menu and
        # not the cascade. In case of (3): the menu actually IS the frame_menu.
        self.config(menu=self.menu)
        self.config(menu=self.frame_menu)

    def register_frame(self,
                       name: str,
                       cls: type,
                       *args, **kwargs):
        ''' Register content frame.

        The frame is only constructed when needed. For that reason, you provide
        the class and initialization arguments.

        Arguments:
            name -- Name to be used in content selection menu
            cls -- Frame class to be displayed
        '''
        if not issubclass(cls, (tkinter.Frame, tkinter.LabelFrame)):
            raise TypeError(f'Provided class [cls] must be a subclass of '
                            f'tkinter\'s Frame but is: {cls}')
        if name in self._frames.keys():
            raise ValueError(f'A frame for {name} was already registered: '
                             f'{self._frames[name].cls}')

        self._frames[name] = FrameInfo(cls, args, kwargs, None)
        # self._update_menu()
        self.frame_menu.add_command(
                label=name, command=lambda: self.show_frame(name))

    def show_frame(self, name):
        ''' Show registered frame by name

        After using register_frame(name, ...), this function will create the
        Frame, if required, and updates the view to show it.

        Arguments:
            name -- name of the frame as per register_frame
        '''
        frame_info = self._get_frame_info(name)
        if frame_info.frame is None:
            frame = self._create_frame(name)
        else:
            frame = frame_info.frame

        self._main_frame = frame
        self._main_frame_name = name
        self._main_frame.tkraise()

    def _create_frame(self, name):
        ''' Create frame from stored class
        '''
        frame_info = self._get_frame_info(name)
        # construct:
        frame = frame_info.cls(self,
                               *(frame_info.args),
                               **(frame_info.kwargs))
        frame.grid(row=0, column=0, sticky='NSWE')
        # store:
        frame_info.frame = frame
        return frame

    def _get_frame_info(self, name) -> FrameInfo:
        if not name:
            return self._dummy_frame
        if name not in self._frames:
            raise KeyError(f'{name} was not registered as frame. '
                           f'I know of: {self._frames.keys()}')
        return self._frames[name]
