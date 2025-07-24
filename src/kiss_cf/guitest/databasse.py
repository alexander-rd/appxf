# The Database class maintains the test case information.
import os
from pathlib import Path
from kiss_cf.storage import Storable, JsonSerializer, LocalStorage
from kiss_cf.setting import SettingDict


class Entry():
    def __init__(self,
                 path:str = '',
                 file:str = '',
                 **kwargs):
        super().__init__(**kwargs)
        self.data = SettingDict(settings={
            'path': (str, path),
            'file': (str, file),
            })

class Database(Storable):
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

    def __init__(self, path: str = 'guitest', **kwargs):
        storage = LocalStorage(
            file='database',
            path=path,
            serializer=JsonSerializer
            )
        super().__init__(storage=storage, **kwargs)
        self.data = SettingDict()
        # all data fields have the same entries
        self.data.set_default_constructor_for_new_keys(
            lambda: Entry().data)
        # all known files will be loaded:
        export_options = SettingDict.ExportOptions()
        export_options.exception_on_new_key = False
        export_options.add_new_keys = True
        self.set_state_kwargs = {'options': export_options}

        # ensure loaded data and initialized database file
        if self.exists():
            self.load()
        else:
            self.store()

    def get_state(self, **kwarg) -> object:
        return self.data.get_state(**kwarg)

    def set_state(self, data: object, **kwarg):
        return self.data.set_state(data, **kwarg)

    def new(self,
            path: str,
            file: str):
        # add new test case file to database
        #
        # If the file was already present, it will remain untouched.
        full_path = Path(path) / file
        self.data[full_path.as_posix()] = Entry(path, file).data

    def remove(self,
               path: str,
               file: str):
        # remove existing test case file from database
        #
        # If path/file does not exist, nothing will happen.
        full_path = Path(path) / file
        print(f'Removing {full_path.as_posix()}')
        del self.data[full_path.as_posix()]
