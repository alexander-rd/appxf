''' APPXF Common GUI Classe

GridFrame: Includes helpers to align frames via tkinter grid.
MainWindow: TopLevel window with configurable buttons on

'''
from typing import Callable
from appxf import logging
import functools

import tkinter

class GridFrame(tkinter.Frame):
    ''' Class to support general APPXF frames

    Frames are cascaded in a grid. RESIZING uses the  row/column weights that
    are supposed to be propagated as follows:
      1) The lowest level frames apply weights dependent on whether they want
         to be resized (weight=1) or not (weight=0).
      2) Any frame provides the sum of weights over it's rows or columns.
    Parents, when placing a frame, consider the sum of weights from (2) for
    their own row/column configuration according to:
      3) The row weight a parent shall apply is the maximum row weight of all
         child frames in this row.
      4) The column weigfht a parent shall apply is the maximum column weight
         of all frames in this column.
    Recommendation is to avoid copmlex matrix grids where and rather subdivide
    a frame either into multiple columns f frames in one row or multiple rows
    of frames in one column.
    '''

    def __init__(self, parent: tkinter.BaseWidget, **kwargs):
        super().__init__(parent, **kwargs)
        # debugging:
        #self.configure(borderwidth=1, relief=tkinter.SOLID)

    def get_total_row_weight(self):
        ''' Get sum of row weights '''
        grid_rows = [widget.grid_info()['row'] for widget in self.grid_slaves()]
        max_row_number = max(grid_rows)
        row_weights = [self.rowconfigure(row).get('weight', 0) for row in range(max_row_number+1)]
        return sum(row_weights)

    def update(self):
        ''' Update frame content

        The implementing frame shall update it's content (like displayed
        values) based on the content containers it received on construction.
        The implementing frame can assume GUI options (like size constraints)
        remain unchanged. In such cases, the user of the frame shall rather
        destroy the frame and recreate it. Default: no implementation.
        '''


class ButtonFrame(GridFrame):
    ''' Window to display a frame with configurable buttons

    All buttons will generate an event <<name>> according to their button
    label.
    '''
    log = logging.getLogger(__name__ + '.ButtonFrame')

    def __init__(self, parent: tkinter.BaseWidget,
                 buttons: list[str],
                 sticky: list[str] = [''],
                 **kwargs):
        '''_summary_

        Arguments:
            parent -- any valid tkinter parent
            buttons -- The bottom row will contain buttons (left to right)
                labeled with the provided strings.

        Keyword Arguments:
            sticky -- apply alignments '', 'E' or 'W' to adjust the layout
                Buttons are aligned in a grid, in the center of the
                cells as default. (default: {['']})
            key_enter_as_button -- handle pressing of the Enter key equal to
                pressing the button name (default: {['']})
        '''
        super().__init__(parent, **kwargs)
        last_button: str | None = None

        # add buttons:
        self.button_frame_list: list[tkinter.Frame] = []
        button_number = 0
        for button in buttons:
            if button_number < len(sticky):
                this_sticky = sticky[button_number]
            else:
                this_sticky = ''
            this_button = tkinter.Button(
                self,
                text=button,
                command=functools.partial(self.handle_button_press, button))
            this_button.grid(row=0, column=button_number, padx=5, pady=5, sticky=this_sticky)
            self.columnconfigure(button_number, weight=1)
            button_number += 1

    def handle_button_press(self, button: str):
        self.log.debug(f'Button press: {button}')
        self.event_generate(f'<<{button}>>')
        self.last_button = button


class FrameWindow(tkinter.Toplevel):
    ''' Window to display a frame with configurable buttons

    Purpose of this class is to apply reuse to Close/Cancel button scenarios.
    It shall also encourage to separate reusable frames which are then provided
    as windows via this class.

    All buttons will generate an event <<name>> according to their button label
    and will write the last event into .last_event. Note that the window
    manager may close the window (like hitting 'X') which will be the event
    WM_DELETE_WINDOW in case the window was closed.
    '''
    def __init__(self, parent: tkinter.BaseWidget,
                 title: str,
                 buttons: list[str],
                 closing: list[str] = [],
                 sticky: list[str] = [],
                 key_enter_as_button: str = '',
                 **kwargs):
        '''_summary_

        Arguments:
            parent -- any valid tkinter parent
            buttons -- The bottom row will contain buttons (left to right)
                labeled with those strings.
            closing -- Button labels that are intended to close the window.

        Keyword Arguments:
            sticky -- apply alignments '', 'E' or 'W' to adjust the layout
                Buttons are aligned in a grid, in the center of the
                cells as default. (default: {['']})
            key_enter_as_button -- handle pressing of the Enter key equal to
                pressing the button name (default: {['']})
        '''
        super().__init__(parent, **kwargs)

        self.title(title)
        # there will only be a single columnn:
        self.columnconfigure(0, weight=1)

        # first row -- plae empty frame
        self.frame = None

        # second row -- button frame (stretch only if frame does not stretch)
        self.button_frame = ButtonFrame(self, buttons=buttons, sticky=sticky)
        self.button_frame.grid(row=1, column=0, sticky='NSEW')

        # add "Enter" handles
        if key_enter_as_button:
            self.bind('<Return>',
                      self.button_frame.handle_button_press(key_enter_as_button))
            self.bind('<KP_Enter>',
                      self.button_frame.handle_button_press(key_enter_as_button))

        # Buttons to close the window:
        for button in closing:
            self.button_frame.bind(f'<<{button}>>', lambda event: self.destroy(), add=True)
        # Closing via window manager:
        self.protocol('WM_DELETE_WINDOW',
                      lambda: self.button_frame.handle_button_press('WM_DELETE_WINDOW'))

    def place_frame(self, frame: GridFrame):
        if self.frame is not None:
            self.frame.destroy()
            self.frame = None
        frame.grid(row=0, column=0, sticky='NSEW')
        frame_row_weight = frame.get_total_row_weight()
        self.rowconfigure(0, weight=frame_row_weight)
        # reconfigure the button row
        self.rowconfigure(1, weight=(1 if frame_row_weight == 0 else 0))

    # any bind on this window shall be intended for the underlying button frame
    def bind(self, sequence=None, func=None, add=None):
        self.button_frame.bind(sequence=sequence, func=func, add=add)
