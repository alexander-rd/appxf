from datetime import datetime
import os.path

from .storage_location import StorageLocation


class LocalStorageLocation(StorageLocation):
    ''' Maintain files in a local path. '''
    def __init__(self, path: str):
        # Ensure the path will exist
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        self.path = path
        # Important: super().__init__() already utilizes the specific
        # implementation. Attributes must be available.
        super().__init__()

    # ## Methods from StorageLocation
    def get_id(self, file: str = '') -> str:
        return self.__class__.__name__ + ': ' + os.path.join(self.path, file)

    # TODO: "file" does not always make sense
    def exists(self, file: str) -> bool:
        return os.path.exists(os.path.join(self.path, file))

    def _get_location_timestamp(self, file: str) -> datetime | None:
        if self.exists(file):
            return datetime.fromtimestamp(os.path.getmtime(
                os.path.join(self.path, file)
                ))
        return None

    def _store(self, file: str, data: bytes):
        with open(os.path.join(self.path, file), 'wb') as f:
            f.write(data)

    def _load(self, file: str) -> bytes:
        with open(os.path.join(self.path, file), 'rb') as f:
            return f.read()

    def _remove(self, file: str):
        full_path = os.path.join(self.path, file)
        if os.path.exists(full_path):
            os.remove(full_path)
