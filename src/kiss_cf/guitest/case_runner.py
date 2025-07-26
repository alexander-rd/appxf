
import argparse
import datetime
import inspect
import json
import markdown
import os
import subprocess
import re
import tkinter
import sys

from tkhtmlview import HTMLLabel
from tkinter import font as tkfont

#from tkhtmlview.html_parser import Defs as html_def
#html_def.DEFAULT_TEXT_FONT_FAMILY = 'TkDefaultFont'
#html_def.FONT_SIZE = 6


# IMPORTANT: appxf modules must not be imported. This guitest module is all
# about supporting manual testing. Test case executions will become obsolete if
# relevant covered lines change. Hence, if this module coveres any additional
# appxf line, all manual test cases would become dependent on those lines.
#
# Exceptions are guitest modules.

# Manual tests are not pytests but general setup (like start of logging) is
# configured in conftest. To enable reuse and import the root path of the
# module is added to the system path:
sys.path.append(os.path.join(os.path.dirname(__file__),'../../../'))
# the following import enables the appxf logging:
from conftest import pytest_runtest_setup
pytest_runtest_setup(None)

# TODO: store test results somehow:
# - invalidate when included library parts changed

# TODO: provide a script to execute all manual tests that are open

# TODO: find a way to start/stop the testing window together with a debug
# window to show states.

#logging.activate_logging(app_scope='kiss_cf')
#for logger_name in logging.logging.Logger.manager.loggerDict:
#    print(logger_name)

class GuitestCaseRunner(tkinter.Tk):
    def __init__(self, explanation: str | None):
        super().__init__()
        self.title('APPXF Manual Test Case Runner')

        self.explanation = explanation.strip() if explanation else ''
        # remove single newlines (wither a full paragraph \n\n or no paragraph
        # at all). The regexp is for \n neither preceeded (?<!\n) nor followed
        # (?!\n) by a newline:
        self.explanation = re.sub(r'(?<!\n)\n(?!\n)', '', self.explanation)

        # argument parsing:
        parser = argparse.ArgumentParser(
            prog=f'{sys.argv[0]}',
            description=(
                'This CaseRunner from APPXF guitest module '
                'was called via above mentioned python script.'
            ))
        parser.add_argument(
            '--result-file',
            required=False, default='',
            help='File to store test results in JSON format.')
        args = parser.parse_args()
        self.result_file = args.result_file

        # timestamp:
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self._get_git_user_info()

        self._build_window()

    def _get_git_user_info(self):
        try:
            self.git_name = subprocess.check_output(
                ["git", "config", "user.name"],
                text=True).strip()
        except subprocess.CalledProcessError:
            self.git_name = 'Unknown GIT User'
        try:
            self.git_email = subprocess.check_output(
                ["git", "config", "user.email"],
                text=True).strip()
        except subprocess.CalledProcessError:
            self.git_email = 'Unknown GIT Email'

    def _build_window(self):
        # Test case explanations:
        self.instruction_label = tkinter.Label(
            self, text='Test Instructions:',
            padx=0, pady=0)
        self.instruction_label.pack(anchor='w', padx=5, pady=0)
        self.instruction_frame = tkinter.Frame(
            bd=1, relief='sunken')
        self.instruction_frame.pack(fill='x', padx=5, pady=0)
        self.instruction_widget = self._get_markdown_label(
            parent=self.instruction_frame,
            markdown_text=self.explanation,
            width=80)
        self.instruction_widget.pack(
            fill='x')

        # Identification label:
        self.observations_label = tkinter.Label(
            self, text='Obervations:',
            padx=0, pady=0)
        self.observations_label.pack(anchor='w', padx=5, pady=0)

        self.observations_info_frame = tkinter.Frame(
            bd=1, relief='sunken')
        self.observations_info_frame.pack(fill='x', padx=5, pady=0)
        self.observations_info_timestamp_label = tkinter.Label(
            self.observations_info_frame,
            text=f'UTC Timestamp: {self.timestamp}',
            justify=tkinter.LEFT)
        self.observations_info_timestamp_label.pack(
            anchor='w', padx=0, pady=0)
        self.observations_info_author_label = tkinter.Label(
            self.observations_info_frame,
            text=f'Author (GIT name <email>): {self.git_name} <{self.git_email}>',
            justify=tkinter.LEFT)
        self.observations_info_author_label.pack(
            anchor='w', padx=0, pady=0)

        # Test results:
        self.observations_text = tkinter.Text(
                self, width=80, height=15)
        self.observations_text.insert('1.0', 'Enter observations...')
        #self.scrollbar = tkinter.Scrollbar(
        #        self, orient=tkinter.VERTICAL,
        #        command=self.entry.yview)  # type: ignore (entry is Text)
        #self.place(self.scrollbar, row=0, column=2,
        #            setting=GridSetting(padx=(0, 5), sticky='NSE'))
        #self.entry.configure(yscrollcommand=self.scrollbar.set)
        self.observations_text.pack(anchor='w', fill='x', padx=5, pady=0)

        # Button Frame
        button_frame = tkinter.Frame(self)
        button_frame.pack()
        # OK Button:
        button_ok = tkinter.Button(
            button_frame, text="OK", command=self.button_ok)
        button_ok.pack(side=tkinter.LEFT)
        # Failed Button:
        button_failed = tkinter.Button(
            button_frame, text="Fail", command=self.button_failed)
        button_failed.pack(side=tkinter.LEFT)

        # TODO: for toplevel, we might want to reopen it.

        # TODO: also for frame tests, we might want to open on demand

        # TODO: needed is a debug window to check some states before/after
        # execution of the window

    def _get_markdown_label(self,
                            parent,
                            markdown_text: str,
                            width: int = 400) -> tkinter.Widget:
        ''' Get label displaying markdown formatted text '''
        # Convert markdown to HTML
        html = markdown.markdown(markdown_text)
        #print(f'Input: {markdown}')
        #print(f'HTML: {html}')
        # adjust font sizes via adding code to paragraphs:
        html = re.sub('<p>', '<p style="font-size: 11px;">', html)
        #print(f'HTML2: {html}')

        # Create HTMLLabel with fixed width
        widget = HTMLLabel(parent, html=html,
                           width=width)

        # Ensure text wraps within width
        #widget.fit_height()  # Adjust height to content
        widget.after(100, lambda: widget.fit_height())

        return widget

    def button_ok(self):
        self._write_result_file('ok')
        self.destroy()

    def button_failed(self):
        self._write_result_file('failed')
        self.destroy()

    def _write_result_file(self, result: str):
        if self.result_file:
            with open(self.result_file, 'w') as file:
                json.dump({
                    'timestamp': f'{self.timestamp}',
                    'author': f'{self.git_name} <{self.git_email}>',
                    'description': self.explanation,
                    'comment': self.observations_text.get('1.0', tkinter.END),
                    'result': result
                    }, file, indent=2)

    def run(self, tkinter_class: type[tkinter.BaseWidget], *args, **kwargs):
        if issubclass(tkinter_class, tkinter.Toplevel):
            self._run_toplevel(tkinter_class, *args, **kwargs)
        elif issubclass(tkinter_class, tkinter.Frame):
            self._run_frame(tkinter_class, *args, **kwargs)


    def _run_frame(self, frame_type: type[tkinter.Frame], *args, **kwargs):
        test_window = tkinter.Toplevel(self)

        test_window.rowconfigure(0, weight=1)
        test_window.columnconfigure(0, weight=1)
        test_window.title('Frame under Test')

        test_frame = frame_type(test_window, *args, **kwargs)
        test_frame.grid(row=0, column=0, sticky='NSWE')

        # place test frame right to control window
        self.place_toplevel(test_window)

        self.mainloop()


    def _run_toplevel(self,
                     toplevel_type: type[tkinter.Toplevel],
                     *args, **kwargs):
        # print out caller docstring
        stack = inspect.stack()
        try:
            # Find the caller's frame
            caller_frame = stack[1]
            caller_module = inspect.getmodule(caller_frame[0])
            if caller_module and caller_module.__doc__:
                print("Caller Module Docstring:")
                print(caller_module.__doc__)
            else:
                print("No docstring available for the caller module.")
        finally:
            del stack  # Clean up to avoid reference cycles

        # window handling
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
