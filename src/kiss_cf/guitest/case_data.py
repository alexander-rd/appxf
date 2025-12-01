''' Providing a helper to maintain test case data '''
import os

from pathlib import Path
from collections import OrderedDict

from kiss_cf.storage import JsonSerializer, LocalStorage
from kiss_cf.setting import SettingDict, SettingSelect, SettingString


class CaseEntry():
    def __init__(self,
                 path:str = '',
                 file:str = '',
                 **kwargs):
        super().__init__(**kwargs)
        self.data = SettingDict(settings={
            'state': SettingSelect(
                base_setting=SettingString(),
                value='new',
                select_map = {state: state for state in [
                    'new', 'valid', 'invalid']},
                # switch off all fency stuff to disable exporting those details
                # into storage:
                mutable_list = False,
                mutable_items = False,
                custom_value = False
                ),
            })

class CaseData():
    # Test cases shall be selected efficiently which is ideally supported by
    # the database storage. The followins layers may exist:
    #  1) Test case library like, unit tests and feature tests in case of
    #     appxf. THIS LEVEL IS NOT SUPPORTED. If this is required, scanner and
    #     test tool need to be ran twice. Or the tool is extended later
    #     supporting multiple data bases.
    #  2) Subfolders until reaching the python file.
    #  3) The python file
    #
    # (2) and (3) will be the the reference for the test case while both will
    # be separate elements for the data element.
    #
    # The database is fixed to use a local, JSON (human readable) storage
    # format.

    def __init__(self,
                 path: str = 'manual_tests',
                 **kwargs):
        super().__init__(**kwargs)
        self.root_path = path
        self.storage_factory = LocalStorage.get_factory(
            path=path,
            serializer=JsonSerializer)
        # initialize data as SettingDict:
        self.case_data = SettingDict(
            storage=self.storage_factory('database'))
        # all data fields have the same entries:
        self.case_data.set_default_constructor_for_new_keys(
            lambda: CaseEntry().data)
        # all known cases will be loaded:
        export_options = SettingDict.ExportOptions()
        export_options.exception_on_missing_key = False
        export_options.exception_on_new_key = False
        export_options.add_new_keys = True
        self.case_data.set_state_kwargs = {'options': export_options}

        # ensure loaded data and initialized database file
        if self.case_data.exists():
            self.case_data.load()
        else:
            self.case_data.store()

    def new(self,
            path: str,
            file: str):
        # add new test case file to database
        #
        # If the file was already present, it will remain untouched.
        full_path = Path(path) / file
        full_path = full_path.as_posix()
        if full_path in self.case_data:
            print(f'Already existing: {full_path}')
        else:
            print(f'Added new to database: {full_path}')
            self.case_data[full_path] = CaseEntry(path, file).data

    def remove(self,
               path: str,
               file: str):
        # remove existing test case file from database
        #
        # If path/file does not exist, nothing will happen.
        full_path = Path(path) / file
        full_path = full_path.as_posix()
        if full_path in self.case_data:
            print(f'Removed from database: {full_path}')
            del self.case_data[full_path]

    def get_case_name(self, case) -> str:
        return Path(case).stem[len('manual_'):]

    def get_case_path_string(self, case: str) -> str:
        return Path(case).parent.as_posix()

    def get_case_string(self, case: str) -> str:
        return f'{self.get_case_path_string(case)}::{self.get_case_name(case)}'

    def get_path_to_case_map(self) -> dict[str, str]:
        self.ensure_sorted()
        map = OrderedDict()
        for case_name in self.case_data:
            path = self.get_case_path_string(case_name)
            case_name = self.get_case_name(case_name)

            if path in map:
                map[path] += [case_name]
            else:
                map[path] = [case_name]
        return map

    def ensure_sorted(self):
        self.case_data.sort()

    def store(self):
        self.ensure_sorted()
        self.case_data.store()

    def load(self):
        self.case_data.load()
