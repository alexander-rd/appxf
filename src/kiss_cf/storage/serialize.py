''' Provide a serialization

This is a small wrapper around pickle to ensure "safe" unpacking the bytes from
the file.

"safe": Unpickling poses a risk of code injection. This is avoided in
deserialize() via RestrictedUnpickler according to pickle documentation:
https://docs.python.org/3/library/pickle.html#restricting-globals.
'''

import pickle
import builtins
import io

class RestrictedUnpickler(pickle.Unpickler):
    '''Class to disable unwanted symbols.'''
    def find_class(self, module, name):
        # Only allow safe classes from builtins.
        if module == "builtins" and name in []:
            return getattr(builtins, name)
        # Forbid everything else.
        raise pickle.UnpicklingError(
            f'global "{module}.{name}" is forbidden', module, name)

def serialize(obj: object) -> bytes:
    ''' Serialize an object

    Important note: include a version numberin your object data in case
    serialization/deserialization algorithm changes.
    '''
    return pickle.dumps(obj)

def deserialize(data: bytes) -> object:
    ''' Deserialize an object

    Important note: include a version numberin your object data in case
    serialization/deserialization algorithm changes.
    '''
    return RestrictedUnpickler(io.BytesIO(data)).load()
