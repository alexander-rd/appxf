''' APPXF Common GUI Classe

GridFrame: Includes helpers to align frames via tkinter grid.
MainWindow: TopLevel window with configurable buttons on

'''
from __future__ import annotations
import functools
import tkinter
from tkinter import ttk
from typing import NamedTuple, Iterable, Callable

from appxf import logging


class AppxfGuiError(Exception):
    ''' Error thrown in context of GUI handling '''


class GridSetting(NamedTuple):
    sticky: str | None = None
    padx: int | None = None
    pady: int | None = None
    row_weight: int | None = None
    column_weight: int | None = None

    def get(self, field: str, default: GridSetting):
        value = getattr(self, field, None)
        if value is None:
            value = getattr(default, field)
        return value


class GridFrame(tkinter.Frame):
    ''' Class to support general APPXF frames

    Widgets/Frames are distinguished into the following categories for default
    settings:
      * no stretching, placement in cell center and padding of 5 (default if
        nothing else fits)
      * horizontally stretching, vertically aligned in center and a padding of
        5 (typical for entry fields)
      * stretching in all dimensions and a padding of 5 (typical for text
        fields)
      * stretching in all dimensions but no padding (typical for any frame only
        holding other content that alrady applied padding)
      * no stretch but aligned to the right with padding of 5 -- currently
        applied for labels AND LIKELY TO CHANGE IN FUTURE

    Frames are cascaded in a grid. RESIZING uses the row/column weights that
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

    log = logging.getLogger(f'{__name__}.GridFrame')

    # Note that the weights are read from it's Frame contents. If it contains
    # widgets, they may sum up to zero. If they contain nothing, the frame
    # weight will be 1.
    frame_setting = GridSetting(
        sticky='EWNS', padx=0, pady=0, row_weight=1, column_weight=1)

    classes_horizontal_stretch_setting = [
        tkinter.Entry, ttk.Entry, ttk.Combobox]
    item_horizontal_stretch_setting = GridSetting(
        sticky='EW', padx=5, pady=5, row_weight=0, column_weight=1)

    classes_full_stretch_setting = [tkinter.Text, ttk.Entry]
    item_full_stretch_setting = GridSetting(
        sticky='EWNS', padx=5, pady=5, row_weight=1, column_weight=1)

    classes_right_aligned_setting = [tkinter.Label]
    item_right_aligned_setting = GridSetting(
        sticky='E', padx=5, pady=5, row_weight=0, column_weight=0)

    # applies to anything else
    item_centered_setting = GridSetting(
        sticky='', padx=5, pady=5, row_weight=0, column_weight=0)

    def __init__(self,
                 parent: tkinter.BaseWidget,
                 row_spread: bool = False,
                 column_spread: bool = False,
                 **kwargs):
        super().__init__(parent, **kwargs)
        self.row_spread: bool = row_spread
        self.column_spread: bool = column_spread
        self.row_weights: dict[int, int] = {}
        self.column_weights: dict[int, int] = {}

    # Consistent would be to stick with widget.grid() for placement but the
    # tkinter grid geometry does not include hooks that can be adjusted in this
    # frame class to support the injection of default values. Hence, the
    # GridFrame needs to provide the method for widget placement.
    def place(self,
              widget: tkinter.Widget | GridFrame,
              row: int,
              column: int,
              setting: GridSetting | None = None):
        ''' Place Widgets/Frames into this Frame, using default settings

        You can always manually place via grid or use rowconfigure and
        columnconfigure to perform adjustments. See the class description for
        applied defaults.
        '''
        if setting is None:
            setting = GridSetting()

        if isinstance(widget, tkinter.Frame):
            default_setting = self.frame_setting
            if isinstance(widget, GridFrame):
                default_setting = default_setting._replace(
                    row_weight=widget.get_total_row_weight(),
                    column_weight=widget.get_total_column_weight())
        elif isinstance(
            widget, tuple(self.classes_horizontal_stretch_setting)):
            default_setting = self.item_horizontal_stretch_setting
        elif isinstance(
            widget, tuple(self.classes_full_stretch_setting)):
            default_setting = self.item_full_stretch_setting
        elif isinstance(
            widget, tuple(self.classes_right_aligned_setting)):
            default_setting = self.item_right_aligned_setting
        else:
            default_setting = self.item_centered_setting
        self.log.debug(
            f'Placing frame {type(widget)} with setting: {default_setting}')
        # TODO: this handling (overwriting) just to get the type warnings that
        # would pop up below right is not sppropriate.
        widget.grid(row=row, column=column,
                    sticky=setting.get('sticky', default_setting),
                    padx=setting.get('padx', default_setting),
                    pady=setting.get('pady', default_setting))
        # apply maximum row/column weights; ">="" is used to ensure the index
        # is written to the dict
        row_weight = setting.get('row_weight', default_setting)
        if row_weight >= self.row_weights.get(row, 0):
            self.row_weights[row] = row_weight
        column_weight = setting.get('column_weight', default_setting)
        if column_weight >= self.column_weights.get(column, 0):
            self.column_weights[column] = column_weight
        self._apply_weights()

    def _apply_weights(self):
        ''' apply row/column weights

        If row_spread/column_spread is True, the rows/columns will get weight=1
        to ensure they are spreading.
        '''
        # row weights depend on whether content of one column should be spread
        # over the rows
        spread = self.column_spread
        if sum(self.row_weights.values()) > 0:
            # if there is any weight, there is no reason to enforce weight=1
            spread = False
        for row, weight in self.row_weights.items():
            self.rowconfigure(row, weight=1 if spread else weight)

        spread = self.row_spread
        if sum(self.column_weights.values()) > 0:
            spread = False
        for column, weight in self.column_weights.items():
            self.columnconfigure(column, weight=1 if spread else weight)

    def get_total_rows(self) -> int:
        ''' Get total number of rows placed in this GridFrame '''
        return max([
            widget.grid_info()['row']
            for widget in self.grid_slaves()])

    def get_total_columns(self) -> int:
        ''' Get total number of columns placed in this GridFrame '''
        return max([
            widget.grid_info()['column']
            for widget in self.grid_slaves()])

    def get_total_row_weight(self):
        ''' Get sum of row weights currently configured '''
        grid_rows = [
            widget.grid_info()['row']
            for widget in self.grid_slaves()]
        if grid_rows:
            max_row_number = max(grid_rows)
            row_weights = [
                self.rowconfigure(row).get('weight', 0)
                for row in range(max_row_number+1)]
        else:
            # If a frame contains nothing, it's typically added to fill up
            # space inbetween content.
            row_weights = [0]
        return sum(row_weights)

    def get_total_column_weight(self):
        ''' Get sum of column weights currently configured '''
        grid_columns = [
            widget.grid_info()['column']
            for widget in self.grid_slaves()]
        if grid_columns:
            max_column_number = max(grid_columns)
            column_weights = [
                self.columnconfigure(row).get('weight', 0)
                for row in range(max_column_number+1)]
        else:
            # If a frame contains nothing, it's typically added to fill up
            # space inbetween content.
            column_weights = [0]
        return sum(column_weights)


class ButtonFrame(GridFrame):
    ''' Window to display a frame with configurable buttons

    All buttons will generate an event <<name>> according to their button
    label.
    '''
    log = logging.getLogger(__name__ + '.ButtonFrame')

    def __init__(self, parent: tkinter.BaseWidget,
                 buttons: Iterable[str],
                 spread: bool = False,
                 **kwargs):
        ''' Frame with buttons left to right

        Arguments:
            parent -- any valid tkinter parent
            buttons -- The bottom row will contain buttons (left to right)
                labeled with the provided strings. Adding a button label ''
                places an empty frame that stretches and fills space.

        Keyword Arguments:
            sticky -- apply alignments '', 'E' or 'W' to adjust the layout
                Buttons are aligned in a grid, in the center of the
                cells as default. (default: {['']})
            key_enter_as_button -- handle pressing of the Enter key equal to
                pressing the button name (default: {['']})

        Provides Events:
            <<Button Name>> according to provided button names.
        '''
        super().__init__(parent,
                         row_spread=spread,
                         **kwargs)
        self.last_event = None

        # add buttons:
        self.button_frame_list: list[tkinter.Frame] = []
        button_number = 0
        for button in buttons:
            if button:
                this_widget = tkinter.Button(
                    self,
                    text=button,
                    command=functools.partial(
                        self.handle_button_press, button))
            else:
                this_widget = GridFrame(self)
            self.place(widget=this_widget, row=0, column=button_number)
            button_number += 1

    def handle_button_press(self, button: str):
        self.log.debug(f'Button press: {button}')
        self.last_event = f'<<{button}>>'
        self.event_generate(f'<<{button}>>')


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
                 buttons: Iterable[str] = ('Cancel', 'OK'),
                 closing: str | list[str] = 'Cancel',
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
        if isinstance(closing, str):
            closing = [closing]

        self.title(title)
        # there will only be a single columnn:
        self.columnconfigure(0, weight=1)

        # first row -- plae empty frame
        self.frame = None

        # second row -- button frame (stretch only if frame does not stretch)
        self.button_frame = ButtonFrame(self, buttons=buttons, spread=True)
        self.button_frame.grid(row=1, column=0, sticky='EWS')

        # add "Enter" handles
        if key_enter_as_button:
            self.bind('<Return>',
                      self.button_frame.handle_button_press(
                          key_enter_as_button))
            self.bind('<KP_Enter>',
                      self.button_frame.handle_button_press(
                          key_enter_as_button))

        # Buttons to close the window:
        for button in closing:
            self.button_frame.bind(
                f'<<{button}>>', lambda event: self.destroy(), add=True)
        # Closing via window manager:
        self.protocol('WM_DELETE_WINDOW',
                      lambda: self.button_frame.handle_button_press(
                          closing[0] if closing else 'WM_DELETE_WINDOW'))

    @property
    def last_event(self) -> str | None:
        ''' Obtain the last triggered event

        Typically required to identify whether the window was cancelled (event
        <<Cancelled>>) or properly exited (event <<OK>>)
        '''
        return self.button_frame.last_event

    def place_frame(self, frame: GridFrame):
        if self.frame is not None:
            self.frame.destroy()
            self.frame = None
        frame.grid(row=0, column=0, sticky='EWNS')
        frame_row_weight = frame.get_total_row_weight()
        self.rowconfigure(0, weight=frame_row_weight)
        # reconfigure the button row
        self.rowconfigure(1, weight=(0 if frame_row_weight else 1))

    # any bind on this window shall be intended for the underlying button frame
    def bind(self,
             sequence: str | None = None,
             func: Callable[[tkinter.Event], object] | None = None,
             add: bool | None = None):
        self.button_frame.bind(sequence=sequence, func=func, add=add)
