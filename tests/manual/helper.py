import tkinter

# TODO: find a way to accumulate coverage as part of the reporting

# TODO: store test results somehow:
# - invalidate when included library parts changed

# TODO: provide a script to execute all manual tests that are open

# TODO: find a way to star/stop the testing window together with a debug window
# to show states.


class ManualTestHelper(tkinter.Tk):
    def __init__(self, explanation: str):

        super().__init__()
        self.title('Test Control')

        self.explanation = explanation.strip()

        explanation_label = tkinter.Label(
            self, text=self.explanation,
            wraplength=450, justify=tkinter.LEFT,
            padx=5, pady=5)
        explanation_label.pack()

        button_ok = tkinter.Button(
            self, text="OK", command=self.button_ok)
        button_ok.pack()

        # TODO: for toplevel, we might want to reopen it.

        # TODO: also for frame tests, we might want to open on demand

        # TODO: needed is a debug window to check some states before/after
        # execution of the window

    def button_ok(self):
        self.destroy()

    def run_frame(self, frame_type: type[tkinter.Frame], *args, **kwargs):
        test_window = tkinter.Toplevel(self)

        test_window.rowconfigure(0, weight=1)
        test_window.columnconfigure(0, weight=1)
        test_window.title('Frame under Test')

        test_frame = frame_type(test_window, *args, **kwargs)
        test_frame.grid(row=0, column=0, sticky='NSWE')

        # place test frame right to control window
        self.place_toplevel(test_window)

        self.mainloop()

    def run_toplevel(self,
                     toplevel_type: type[tkinter.Toplevel],
                     *args, **kwargs):
        test_window = toplevel_type(self, *args, **kwargs)
        # test_window.grab_set()
        self.place_toplevel(test_window)
        self.mainloop()

    def place_toplevel(self, toplevel: tkinter.Toplevel):
        '''Place a toplevel to the right of the control window.'''
        self.update()
        toplevel.update()
        toplevel.geometry('%dx%d+%d+%d' % (
            toplevel.winfo_width(),
            toplevel.winfo_height(),
            self.winfo_x() + self.winfo_width() + 10,
            self.winfo_y()))


class ManualTestFrame(tkinter.Toplevel):
    def __init__(self, parent, frame_type, *args, **kwargs):
        root = tkinter.Tk()
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        test_frame = frame_type(root, *args, **kwargs)
        test_frame.grid(row=1, column=0, sticky='NSWE')
