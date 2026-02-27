# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
'''Manual Test Runner

Call via:  ./.venv/bin/python manual_tests.py

Virtual environment (venv) is required since, without, appxf would be unknown.
'''

from appxf_matema import CaseData, CmdHelper, Scanner

case_data = CaseData()

scanner = Scanner(case_data=case_data, path=['tests', 'tests_features'])
scanner.scan()

cmd_helper = CmdHelper(database=case_data)
cmd_helper.run()
