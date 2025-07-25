# The Database class maintains the test case information.
import os
from pathlib import Path
from kiss_cf.storage import Storable, JsonSerializer, LocalStorage
from kiss_cf.setting import SettingDict, SettingSelect, SettingString


class Entry():
    def __init__(self,
                 path:str = '',
                 file:str = '',
                 **kwargs):
        super().__init__(**kwargs)
        self.data = SettingDict(settings={
            'path': (str, path),
            'file': (str, file),
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

class Database():
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

    def __init__(self, path: str = 'guitest', **kwargs):
        super().__init__(**kwargs)
        self.storage_factory = LocalStorage.get_factory(
            path=path,
            serializer=JsonSerializer)
        # initialize data as SettingDict:
        self.data = SettingDict(
            storage=self.storage_factory('database'))
        # all data fields have the same entries:
        self.data.set_default_constructor_for_new_keys(
            lambda: Entry().data)
        # all known cases will be loaded:
        export_options = SettingDict.ExportOptions()
        export_options.exception_on_missing_key = False
        export_options.exception_on_new_key = False
        export_options.add_new_keys = True
        self.data.set_state_kwargs = {'options': export_options}

        # ensure loaded data and initialized database file
        if self.data.exists():
            self.data.load()
        else:
            self.data.store()

    def new(self,
            path: str,
            file: str):
        # add new test case file to database
        #
        # If the file was already present, it will remain untouched.
        full_path = Path(path) / file
        full_path = full_path.as_posix()
        if full_path in self.data:
            print(f'Already existing: {full_path}')
        else:
            print(f'Added new to database: {full_path}')
            self.data[full_path] = Entry(path, file).data

    def remove(self,
               path: str,
               file: str):
        # remove existing test case file from database
        #
        # If path/file does not exist, nothing will happen.
        full_path = Path(path) / file
        full_path = full_path.as_posix()
        if full_path in self.data:
            print(f'Removed from database: {full_path}')
            del self.data[full_path]

    def store(self):
        self.data.store()

    def load(self):
        self.data.load()