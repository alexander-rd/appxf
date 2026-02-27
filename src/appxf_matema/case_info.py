# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
import datetime
import re
from functools import cached_property

from appxf_matema.case_parser import CaseParser


class CaseInfo:
    def __init__(self, parser: CaseParser | None, disable_parsing: bool = False):
        # # Take over arguments
        self._case_parser = parser
        self._disable_parsing = disable_parsing

    # TODO: no one calls self._case_parser.parse(), yet

    @cached_property
    def explanation(self):
        """test case description"""
        self._ensure_parsed()

        if self._case_parser:
            explanation = self._case_parser.caller_module_docstring
        else:
            explanation = "Test case parsing was disabled."

        explanation = explanation.strip() if explanation else ""
        # remove single newlines (either a full paragraph \n\n or no paragraph
        # at all). The regexp is for \n neither preceeded (?<!\n) nor followed
        # (?!\n) by a newline:
        explanation = re.sub(r"(?<!\n)\n(?!\n)", "", explanation)
        return explanation

    @cached_property
    def timestamp(self):
        return datetime.datetime.now(datetime.timezone.utc)

    def _ensure_parsed(self):
        if self._case_parser and not self._case_parser.parsed:
            self._case_parser.parse()

    def get_symbol_from_case_module(self, function_name: str):
        """get symbol by name from test case module

        Initial use case was getting hook functions like: process_*() or
        setup() from the function model.
        """
        self._ensure_parsed()
        # Execute the requested function with setup/teardown
        if not self._case_parser:
            raise ValueError("Parsing was disabled")
        if not hasattr(self._case_parser.module, function_name):
            raise ValueError(
                f"Function {function_name} does not exist in {self._case_parser.module}"
            )
        return getattr(self._case_parser.module, function_name)
