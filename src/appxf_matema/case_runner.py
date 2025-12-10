
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
from appxf import logging
from appxf_matema.case_parser import CaseParser

# IMPORTANT: appxf modules must not be imported. This manual-test support
# module is all about supporting manual testing. Test case executions will
# become obsolete if relevant covered lines change. Hence, if this module
# coveres any additional appxf line, all manual test cases would become
# dependent on those lines.
#
# Exceptions may be the manual-test modules.

# Manual tests are not pytests but general setup (like start of logging) is
# configured in conftest. To enable reuse and import the root path of the
# module is added to the system path:
sys.path.append(os.path.join(os.path.dirname(__file__),'../../../'))
# the following import enables the appxf logging:
logging.activate_logging('appxf_matema')
#from conftest import pytest_runtest_setup
#pytest_runtest_setup(None)

# TODO: store test results somehow:
# - invalidate when included library parts changed

# TODO: provide a script to execute all manual tests that are open

# TODO: find a way to start/stop the testing window together with a debug
# window to show states.

#logging.activate_logging(app_scope='kiss_cf')
#for logger_name in logging.logging.Logger.manager.loggerDict:
#    print(logger_name)

class CaseRunnerGui:
    '''GUI container for manual test case runner.

    Encapsulates the tkinter window and related UI components.
    '''
    def __init__(
            self,
            tk_root: tkinter.Tk,
            extra_button_frame: tkinter.Frame,
            observations_text: tkinter.Text
            ):
        self.tk = tk_root
        self.extra_button_frame = extra_button_frame
        self.observations_text = observations_text


class ManualCaseRunner:
    def __init__(self, explanation: str = ''):

        # Get the module that instantiated the case runner. Frame 0 will be the
        # CaseParser __init__, frame 1 is this __init__ and frame 2 will be
        # within the module that called this Case Runner.
        self.case_parser = CaseParser(frame_index=2)

        if not explanation:
            explanation = self.case_parser.caller_module_docstring

        self.explanation = explanation.strip() if explanation else ''
        # remove single newlines (wither a full paragraph \n\n or no paragraph
        # at all). The regexp is for \n neither preceeded (?<!\n) nor followed
        # (?!\n) by a newline:
        self.explanation = re.sub(r'(?<!\n)\n(?!\n)', '', self.explanation)

        # argument parsing:
        parser = argparse.ArgumentParser(
            prog=f'{sys.argv[0]}',
            description=(
                'This CaseRunner from the APPXF manual test module '
                'was called via above mentioned python script.'
            ))
        parser.add_argument(
            '--result-file',
            required=False, default='',
            help='File to store test results in JSON format.')
        self._add_arguments_from_caller(parser)
        self.argparse_result = parser.parse_args()

        # timestamp:
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self._get_git_user_info()

    def _add_arguments_from_caller(self, parser: argparse.ArgumentParser):
        for function, summary in self.case_parser.caller_module_function_map.items():
            if function.startswith('process_'):
                parser.add_argument(
                    f'--{function}',
                    action='store_true',
                    help=summary)


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

    def _get_main_window(self) -> CaseRunnerGui:
        """Build and return the main control window GUI without calling mainloop."""
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
            markdown_text=self.explanation,
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
            text=f'UTC Timestamp: {self.timestamp}',
            justify=tkinter.LEFT)
        observations_info_timestamp_label.pack(
            anchor='w', padx=0, pady=0)
        observations_info_author_label = tkinter.Label(
            observations_info_frame,
            text=f'Author (GIT name <email>): {self.git_name} <{self.git_email}>',
            justify=tkinter.LEFT)
        observations_info_author_label.pack(
            anchor='w', padx=0, pady=0)

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

        # Create the CaseRunnerGui object that will be passed to button callbacks
        gui = CaseRunnerGui(root, extra_button_frame, observations_text)

        # OK Button:
        button_ok = tkinter.Button(
            button_frame, text="OK", command=lambda: self.button_ok(gui))
        button_ok.pack(side=tkinter.LEFT)
        # Failed Button:
        button_failed = tkinter.Button(
            button_frame, text="Fail", command=lambda: self.button_failed(gui))
        button_failed.pack(side=tkinter.LEFT)

        # TODO: for toplevel, we might want to reopen it.

        # TODO: also for frame tests, we might want to open on demand

        # TODO: needed is a debug window to check some states before/after
        # execution of the window

        return gui

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

    def button_ok(self, gui: CaseRunnerGui):
        self._write_result_file('ok', gui)
        gui.tk.destroy()

    def button_failed(self, gui: CaseRunnerGui):
        self._write_result_file('failed', gui)
        gui.tk.destroy()

    def _write_result_file(self, result: str, gui: CaseRunnerGui = None):
        if self.argparse_result.result_file:
            comment = ''
            if gui:
                comment = gui.observations_text.get('1.0', tkinter.END)
            with open(self.argparse_result.result_file, 'w', encoding='utf-8') as file:
                json.dump({
                    'timestamp': f'{self.timestamp}',
                    'author': f'{self.git_name} <{self.git_email}>',
                    'description': self.explanation,
                    'comment': comment,
                    'result': result
                    }, file, indent=2)

    def run(self, tkinter_class: type[tkinter.BaseWidget], *args, **kwargs):
        gui = self._get_main_window()
        if issubclass(tkinter_class, tkinter.Toplevel):
            self._run_toplevel(gui, tkinter_class, *args, **kwargs)
        elif issubclass(tkinter_class, tkinter.Frame):
            self._run_frame(gui, tkinter_class, *args, **kwargs)
        else:
            raise TypeError(
                f'Provided tkinter class {tkinter_class.__class__}'
                f'is not supported. Supported are: '
                f'TopLevel, Frame.')
        gui.tk.mainloop()

    def run_by_file_parsing(self):
        '''Execute process functions via command-line arguments or button interface.

        Checks if any --process_* arguments were passed. If yes, executes the
        corresponding function. If no, creates buttons for each process_* function
        that spawn Python subprocesses with the appropriate --process_* flag.

        Only one --process_* argument is expected at a time. If multiple are passed,
        only the first is executed (unexpected but handled gracefully).
        '''
        # Find the first --process_* argument that was passed via command line
        process_arg = None
        for arg in vars(self.argparse_result):
            if arg.startswith('process_') and getattr(self.argparse_result, arg):
                process_arg = arg
                break

        if process_arg:
            # Execute the requested function
            if hasattr(self.case_parser.module, process_arg):
                function = getattr(self.case_parser.module, process_arg)
                function()
        else:
            # No process argument passed: create buttons for process_* functions
            gui = self._get_main_window()
            for function_name, summary in self.case_parser.caller_module_function_map.items():
                if function_name.startswith('process_'):
                    self._add_subprocess_button(
                        gui,
                        function_name,
                        self.case_parser.caller_module_path)
            gui.tk.update()
            gui.tk.mainloop()

    def _add_subprocess_button(self, gui: CaseRunnerGui, process_function_name: str, module_path: str):
        '''Add a button that spawns a subprocess to execute a process function.'''
        def spawn_process():
            subprocess.run(
                [sys.executable, module_path, f'--{process_function_name}'],
                check=False)

        button = tkinter.Button(
            gui.extra_button_frame,
            text=process_function_name,
            command=spawn_process)
        button.pack(side=tkinter.LEFT)

    def _run_frame(self, gui: CaseRunnerGui, frame_type: type[tkinter.Frame], *args, **kwargs):
        test_window = tkinter.Toplevel(gui.tk)

        test_window.rowconfigure(0, weight=1)
        test_window.columnconfigure(0, weight=1)
        test_window.title('Frame under Test')

        test_frame = frame_type(test_window, *args, **kwargs)
        test_frame.grid(row=0, column=0, sticky='NSWE')

        # place test frame right to control window
        self.place_toplevel(gui.tk, test_window)


    def _run_toplevel(self, gui: CaseRunnerGui,
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
        test_window = toplevel_type(gui.tk, *args, **kwargs)
        # test_window.grab_set()
        self.place_toplevel(gui.tk, test_window)

    def place_toplevel(self, root: tkinter.Tk, toplevel: tkinter.Toplevel):
        '''Place a toplevel to the right of the control window.'''
        root.update()
        toplevel.update()
        toplevel.geometry('%dx%d+%d+%d' % (
            toplevel.winfo_width(),
            toplevel.winfo_height(),
            root.winfo_x() + root.winfo_width() + 10,
            root.winfo_y()))


class ManualTestFrame(tkinter.Toplevel):
    def __init__(self, parent, frame_type, *args, **kwargs):
        root = tkinter.Tk()
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        test_frame = frame_type(root, *args, **kwargs)
        test_frame.grid(row=1, column=0, sticky='NSWE')
