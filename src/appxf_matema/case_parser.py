# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0

import inspect


class CaseParser:
    def __init__(self, stack_index: int = 0):
        # caller should not be aware of this __init__ adding a level of stack:
        stack_index += 1
        stack = inspect.stack()
        self._frame = stack[stack_index].frame
        self.parsed: bool = False

    # TODO: this class is not safe to use. Just parse defines the attributes
    # others rely on such that things will crash if no one calls parse() before
    # accessing them.

    def parse(self):
        self.module = inspect.getmodule(self._frame)

        if self.module:
            self.caller_module_name = self.module.__name__
            self.caller_module_path = self.module.__file__ or 'Unknown'
            self.caller_module_docstring = self.module.__doc__ or 'No docstring'

            # Extract all defined functions (not imported)
            self.caller_module_functions = []
            self.caller_module_function_map = {}
            for name, obj in inspect.getmembers(self.module):
                if inspect.isfunction(obj) and obj.__module__ == self.module.__name__:
                    self.caller_module_functions.append(name)
                    # Extract first paragraph (summary) of docstring
                    # per PEP 257
                    docstring = obj.__doc__ or ''
                    # Get text before first blank line (or entire docstring
                    # if no blank line)
                    parts = docstring.split('\n\n')
                    summary = parts[0].strip()
                    # Collapse multi-line summary into single line
                    summary = ' '.join(summary.split())
                    self.caller_module_function_map[name] = summary
        else:
            self.caller_module_name = ''
            self.caller_module_path = ''
            self.caller_module_docstring = ''
            self.caller_module_functions = []
            self.caller_module_function_map = {}

        self.parsed = True
        # self.report()

    def report(self):
        print(
            f'CaseParser identified module: {self.caller_module_name}\n'
            f'path: {self.caller_module_path}\n'
            f'functions: {self.caller_module_functions}\n'
            f'as map: {self.caller_module_function_map}\n'
            f'docstring: {self.caller_module_docstring}'
        )
