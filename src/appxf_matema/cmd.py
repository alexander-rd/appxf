# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
''' Command line helper to inspect and run cases '''
import subprocess
import sys
import os
from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from .case_data import CaseData


class CmdHelper:
    def __init__(self,
                 database: CaseData):
        self.database = database

    def print_case_summary(self):
        print('Summary on test cases in database: ')
        map = self.database.get_path_to_case_map()
        for path, cases in map.items():
            print(f'  {path}:')
            for case in cases:
                print(f'    {case}')

    def select_case(self, text: str = 'Test Case: ') -> str:
        self.print_case_summary()
        case_completer = WordCompleter(list(self.database.case_data.keys()))
        return prompt(text, completer=case_completer)

    def run(self):
        while True:
            case = self.select_case('Which case to run?: ')
            if case not in self.database.case_data:
                print('Exiting since case does not exist.')
                break
            print(f'Running {case}')
            self.run_case(case)

    def run_case(self, case_name: str):
        out_path = Path(
            self.database.root_path,
            self.database.get_case_path_string(case_name),
        )
        coverage_file = out_path / (
            self.database.get_case_name(case_name) + '.coverage'
        )
        result_file = out_path / (
            self.database.get_case_name(case_name) + '.result.json'
        )
        # Extend python ENV to local path from where THIS is called. If not,
        # python assumes the path of the called subprocess and imports may not
        # work as expected.
        env = os.environ.copy()
        existing = env.get('PYTHONPATH', '')
        env['PYTHONPATH'] = os.pathsep.join([existing, '.']).strip(os.pathsep)
        subprocess.run([
            sys.executable,
            '-m', 'coverage', 'run',
            '--source=appxf',
            '--branch',
            f'--data-file={coverage_file}',
            case_name,
            f'--result-file={result_file}'
            ],
            check=True,
            env=env)

        # Optional: Combine results if running multiple times
        # subprocess.run([sys.executable, "-m", "coverage", "combine"],
        #               check=True)
        # subprocess.run([sys.executable, "-m", "coverage", "report"],
        #               check=True)
