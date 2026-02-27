# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import subprocess
import sys
import tkinter
from functools import cached_property

from appxf import logging
from appxf_matema.case_info import CaseInfo
from appxf_matema.case_parser import CaseParser
from appxf_matema.case_runner_gui import CaseRunnerGui
from appxf_matema.git_info import GitInfo


class ManualCaseRunner:
    """Interface Wrapper for Test Cases

    The interfaces include:
     * MaTeMa input arguments and output result writing (via TBD CaseInfo)
     * spawning test case processes (via --process_* CLI arguments)
     * spawning the GUI
     * handling test case execution: setup(), teardown(), test()
        * includes logging and coverage activation
    """

    log = logging.get_logger(__name__ + ".ManualCaseRunner")

    def __init__(
        self,
        logging_context: str = "",
        disable_parsing: bool = False,
        parent: tkinter.Tk | None = None,
    ):
        self._parent = parent
        self._disable_parsing = disable_parsing
        # Note: using logging_context = '' will activate any logging since
        # settings for '' will be inherited from anything on top.
        self._logging_context = logging_context

        # # Initialize self states
        self._logging_activated: bool = False

        self._case_parser: CaseParser | None = None

        # only dip into processing if there are command line arguments (either
        # from a MaTeMa call or from a call via CaseRunner (process_*).
        if len(sys.argv) > 1:
            # initialize case info and parser from here. Stack index should be:
            #   0) this __init__
            #   1) the module calling CaseRunner
            self.ensure_case_parser()
            self._handle_cli_arguments()
        # in any other case, this is just a manual call of the test case where
        # NO additional processing is expected. Eventually, there is a run()
        # call, later.

    # Note: the following cannot be provided as public property since the
    # parser must be instantiated properly
    @cached_property
    def case_info(self) -> CaseInfo:
        return CaseInfo(parser=self.case_parser)

    @cached_property
    def git_info(self) -> GitInfo:
        return GitInfo()

    @cached_property
    def gui(self):
        return CaseRunnerGui(
            case_info=self.case_info, git_info=self.git_info, parent=self._parent
        )

    @cached_property
    def argparse_result(self):
        parser = argparse.ArgumentParser(
            prog=f"{sys.argv[0]}",
            description=(
                "This CaseRunner from APPXF MaTeMa "
                "was called via above mentioned python script."
            ),
        )
        parser.add_argument(
            "--result-file",
            required=False,
            default="",
            help="File to store test results in JSON format.",
        )
        return parser.parse_args()

    @property
    def case_parser(self):
        if not self._case_parser:
            raise RuntimeError(
                "You have to call ensure_case_parser() before using "
                "anything dependentet on the case_parser (like case_info)."
                "Rationale: you have to provide the required stack index"
                "to identify the right test case module."
            )
        # TODO: theoretically, I can traverse the whole stack until I find the
        # first module named "manual_*" but this would make the naming
        # convention also valid for CaseRunner
        return self._case_parser

    def ensure_case_parser(self, stack_index: int = 1):
        if not self._disable_parsing:
            self._case_parser = CaseParser(stack_index=stack_index + 1)
            self._case_parser.parse()

    def _handle_cli_arguments(self):
        # We do not parse process calls from here because process calls shall
        # only be active when used with run() and this call is still pending.

        # TODO: MaTeMa handling is not yet defined. Steps are only outlined,
        # below.

        # 1) parse arguments to get MaTeMa settings
        # 2) Parse file to get further information
        # 3) Initialize the GUI
        # 4) Initialize test (with logging and coverage)
        #     - will depend on parsing results
        pass

    def _handle_process_calls(self) -> bool:
        """execute process call and return true if existent"""
        process_arg = None
        for arg in sys.argv:
            if arg.startswith("--process_"):
                process_arg = arg
                break
        if process_arg:
            function = self.case_info.get_symbol_from_case_module(process_arg[2:])
            self.ensure_logging()
            function()
            return True
        return False

    def ensure_logging(self):
        if self._logging_activated:
            return
        logging.activate_logging(self._logging_context, directory=".testing/log")
        self.log.debug(f"Enabled logging via {__class__.__name__}")
        self._logging_activated = True

    def _write_result_file(self, result: str, gui: CaseRunnerGui = None):
        if self.argparse_result.result_file:
            comment = ""
            if gui:
                comment = self.gui.get_observations_text()
            with open(self.argparse_result.result_file, "w", encoding="utf-8") as file:
                json.dump(
                    {
                        "timestamp": f"{self.case_info.timestamp}",
                        "author": (
                            f"{self.git_info.user_name} <{self.git_info.user_email}>"
                        ),
                        "description": self.case_info.explanation,
                        "comment": comment,
                        "result": result,
                    },
                    file,
                    indent=2,
                )

    def run(self, item: type[tkinter.BaseWidget] | None = None, *args, **kwargs):
        # ensure parsing is initialized, stack indexing from here is:
        #  0) this run()
        #  1) the calling module
        self.ensure_case_parser(stack_index=1)

        # Parse for process calls and execute them. If there was a process
        # call, there is nothing more to handle.
        if self._handle_process_calls():
            return

        if item is None:
            # test case is running by provided functions process_*() or test()
            # or even by instances created directly within the module.
            pass
        elif issubclass(item, tkinter.Toplevel):
            self.ensure_logging()
            self._run_toplevel(item, *args, **kwargs)
        elif issubclass(item, tkinter.Frame) or issubclass(item, tkinter.LabelFrame):
            self.ensure_logging()
            self._run_frame(item, *args, **kwargs)
        else:
            raise TypeError(
                f"Provided item class {item.__class__} "
                "is not supported. Supported are: TopLevel, Frame."
            )

        self._parse_process_hooks()
        self._start_case_runner()

    def _start_case_runner(self, *args, **kwargs):
        """Handle startup and teardown for case runner execution.

        Calls setup() function from the tested module if it exists, executes
        the main function with GUI, then calls teardown() if it exists.
        """
        if hasattr(self.case_parser.module, "setup_once"):
            setup_func = getattr(self.case_parser.module, "setup_once")
            setup_func()
        # Call setup() if it exists in the tested module
        if hasattr(self.case_parser.module, "setup"):
            setup_func = getattr(self.case_parser.module, "setup")
            setup_func()
        try:
            # Execute the main case runner function
            self.gui.tk.mainloop()
        finally:
            # Call teardown() if it exists in the tested module
            if hasattr(self.case_parser.module, "teardown"):
                teardown_func = getattr(self.case_parser.module, "teardown")
                teardown_func()

    def _parse_process_hooks(self):
        """Parse module for process hooks and add to test case GUI

        Creates buttons for each process_* function. CaseRunner will spawn a
        new python process, executing this function whenever the button is
        pressed.
        """
        for (
            function_name,
            summary,
        ) in self.case_parser.caller_module_function_map.items():
            if function_name.startswith("process_"):
                self.gui.add_process_button(
                    command=self._get_process_hook(function_name, summary),
                    label=summary if summary else function_name,
                )

            # update the window:
            self.gui.wm.update()

    def _get_process_hook(self, function_name: str, summary: str):
        def run_process():
            subprocess.run(
                [
                    sys.executable,
                    self.case_parser.caller_module_path,
                    f"--{function_name}",
                ],
                check=False,
            )

        return run_process

    def _run_frame(
        self,
        frame_type: type[tkinter.Frame],
        *args,
        **kwargs,
    ):
        test_window = tkinter.Toplevel(self.gui.tk)

        test_window.rowconfigure(0, weight=1)
        test_window.columnconfigure(0, weight=1)
        test_window.title("Frame under Test")

        test_frame = frame_type(test_window, *args, **kwargs)
        test_frame.grid(row=0, column=0, sticky="NSWE")

        # place test frame right to control window
        self.gui.place_toplevel(test_window)

    def _run_toplevel(
        self,
        toplevel_type: type[tkinter.Toplevel],
        *args,
        **kwargs,
    ):
        test_window = toplevel_type(self.gui.tk, *args, **kwargs)
        self.gui.place_toplevel(test_window)
