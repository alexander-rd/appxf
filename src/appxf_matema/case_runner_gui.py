# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
# TODO: store test results somehow:
# - invalidate when included library parts changed

# TODO: provide a script to execute all manual tests that are open

# TODO: find a way to start/stop the testing window together with a debug
# window to show states.
import re
import tkinter
from dataclasses import dataclass
from functools import cached_property
from typing import Callable

import markdown
from tkhtmlview import HTMLLabel

from appxf_matema.case_info import CaseInfo
from appxf_matema.git_info import GitInfo


class CaseRunnerGui:
    '''GUI container for manual test case runner.

    Encapsulates the tkinter window and related UI components.
    '''
    def __init__(
            self,
            case_info: CaseInfo,
            git_info: GitInfo,
            parent: tkinter.Tk | None = None,
            ):
        self._case_info = case_info
        self._git_info = git_info
        self._parent = parent
        self._result = 'aborted'

    @dataclass(eq=False, order=False, frozen=True)
    class GuiStructure:
        wm: tkinter.Wm
        process_button_frame: tkinter.Frame
        observations_text: tkinter.Text

    # #################
    # Property Access
    # /

    # ## Status related properties
    @property
    def result(self):
        return self._result

    # ## GUI related properties
    @cached_property
    def tk(self) -> tkinter.Tk:
        ''' Obtain the main Tk instance

        In case CaseRunner was called with a parent, this may differ.
        '''
        if isinstance(self.wm, tkinter.Tk):
            return self.wm
        if not isinstance(self._parent, tkinter.Tk):
            raise ValueError(
                f'CaseRunner and CaseRunnerGui '
                f'must be called with tkinter.Tk as parent but parent '
                f'hat type {type(self._parent)}.')
        return self._parent

    @cached_property
    def wm(self):
        ''' Return the window manager of the CaseRunnerGui

        This is either a tkinter Tk or Toplevel instance. Toplevel is used if
        the test case already creates a Tk and passes it as parent to the
        CaseRunner.
        '''
        return self.gui_structure.wm

    @cached_property
    def gui_structure(self):
        return self._get_main_window()

    def get_observations_text(self) -> str:
        ''' Get observations from manual test execution as string'''
        return self.gui_structure.observations_text.get('1.0', tkinter.END)

    def _get_main_window(self) -> GuiStructure:
        ''' Build and return the main control window GUI
        without calling mainloop.
        '''
        root = tkinter.Tk()
        root.title('APPXF Manual Test Case Runner')

        # Test case explanations:
        instruction_label = tkinter.Label(
            root, text='Test Instructions:',
            padx=0, pady=0)
        instruction_label.pack(anchor='w', padx=5, pady=0)
        instruction_frame = tkinter.Frame(
            root, bd=1, relief='sunken')
        instruction_frame.pack(fill='x', padx=5, pady=0)
        instruction_widget = self._get_markdown_label(
            parent=instruction_frame,
            markdown_text=self._case_info.explanation,
            width=80)
        instruction_widget.pack(
            fill='x')

        # Identification label:
        observations_label = tkinter.Label(
            root, text='Obervations:',
            padx=0, pady=0)
        observations_label.pack(anchor='w', padx=5, pady=0)

        observations_info_frame = tkinter.Frame(
            root, bd=1, relief='sunken')
        observations_info_frame.pack(fill='x', padx=5, pady=0)
        observations_info_timestamp_label = tkinter.Label(
            observations_info_frame,
            text=(
                f'UTC Timestamp: {self._case_info.timestamp}',
            ),
            justify=tkinter.LEFT,
        )
        observations_info_timestamp_label.pack(
            anchor='w', padx=0, pady=0)
        observations_info_author_label = tkinter.Label(
            observations_info_frame,
            text=(
                'Author (GIT name <email>): '
                f'{self._git_info.user_name} '
                f'<{self._git_info.user_email}>'
            ),
            justify=tkinter.LEFT,
        )
        observations_info_author_label.pack(anchor='w', padx=0, pady=0)

        # Test results:
        observations_text = tkinter.Text(
                root, width=80, height=15)
        observations_text.insert('1.0', 'Enter observations...')
        observations_text.pack(anchor='w', fill='x', padx=5, pady=0)

        # an empty button frame between observations nad fail/OK buttons.
        extra_button_frame = tkinter.Frame(root)
        extra_button_frame.pack()

        # Button Frame
        button_frame = tkinter.Frame(root)
        button_frame.pack()

        # Create the CaseRunnerGui object that will be passed to
        # button callbacks
        gui_structure = self.GuiStructure(
            wm=root,
            process_button_frame=extra_button_frame,
            observations_text=observations_text
            )

        # OK Button:
        button_ok = tkinter.Button(
            button_frame,
            text="OK",
            command=lambda: self.button_ok(),
        )
        button_ok.pack(side=tkinter.LEFT)
        # Failed Button:
        button_failed = tkinter.Button(
            button_frame,
            text="Fail",
            command=lambda: self.button_failed(),
        )
        button_failed.pack(side=tkinter.LEFT)

        # TODO: for toplevel, we might want to reopen it.

        # TODO: also for frame tests, we might want to open on demand

        # TODO: needed is a debug window to check some states before/after
        # execution of the window

        return gui_structure

    def _get_markdown_label(self,
                            parent,
                            markdown_text: str,
                            width: int = 400) -> tkinter.Widget:
        ''' Get label displaying markdown formatted text '''
        # Convert markdown to HTML
        html = markdown.markdown(markdown_text)
        # adjust font sizes via adding code to paragraphs:
        html = re.sub('<p>', '<p style="font-size: 11px;">', html)

        # Create HTMLLabel with fixed width
        widget = HTMLLabel(parent, html=html,
                           width=width)

        # Ensure text wraps within width
        # widget.fit_height()  # Adjust height to content
        widget.after(100, lambda: widget.fit_height())

        return widget

    def button_ok(self):
        self._result = 'ok'
        self.wm.destroy()

    def button_failed(self):
        self._result = 'failed'
        self.wm.destroy()

    def add_process_button(
            self,
            command: Callable,
            label: str,
        ):
        '''Add a button that spawns a subprocess to execute a
        process function.'''
        button = tkinter.Button(
            self.gui_structure.process_button_frame,
            text=label,
            command=command,
        )
        button.pack(side=tkinter.LEFT)

    def place_toplevel(self, top_level: tkinter.Toplevel):
        '''Place a toplevel to the right of CaseRunnerGui control window'''
        self.tk.update()
        top_level.update()
        geom = '%dx%d+%d+%d' % (
            top_level.winfo_width(),
            top_level.winfo_height(),
            self.tk.winfo_x() + self.tk.winfo_width() + 10,
            self.tk.winfo_y(),
        )
        top_level.geometry(geom)