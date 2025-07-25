''' Command line helper to inspect and run cases '''
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from .database import Database

class CmdHelper():
    def __init__(self,
                 database: Database):
        self.database = database

    def print_case_summary(self):
        print('Summary on test cases in database: ')
        for path, case in self.database.data.items():
            print(f'  {path} [{case['state']}]')

    def select_case(self, text: str = 'Test Case: ') -> str:
        self.print_case_summary()
        case_completer = WordCompleter(list(self.database.data.keys()))
        return prompt(text, completer=case_completer)

    def run(self):
        while True:
            case = self.select_case('Which case to run?: ')
            if case not in self.database.data:
                print('Exiting since case does not exist.')
                break
            print(f'Running {case}')