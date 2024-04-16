from copy import deepcopy
import functools
import typing
import pickle

from . import logging
from kiss_cf.storage import Storable, Storage, StorageMethodDummy

log = logging.getLogger(__name__)


class Buffer(Storable):
    '''Helper to organize data buffering.

    What plus input: When you store or retrieve data, you pass "what (type of)
    data" and the corresponding input (as string). Splitting the "what" is done
    to allow a reset of a specific type of data (later). Note that having the
    input as simple string makes this class flexible but limits it's usage to
    "simple" inputs.

    Implementation ensures that the data passed into and retrieved from the
    buffer is independent. Changes you do in the code does not affect the
    buffered data.
    '''

    log = logging.getLogger(f'{__name__}.Buffer')

    def __init__(self,
                 storage_handler: Storage = StorageMethodDummy(),
                 **kwargs
                 ):

        super().__init__(storage_handler, **kwargs)
        self.buffer = dict()
        self.initially_loaded = False

    def ensure_loaded(self):
        if not self.initially_loaded:
            self.load()
            self.initially_loaded = True

    def isbuffered(self, what: str, input: str):
        '''Check if what/input is buffered'''
        self.ensure_loaded()
        if what in self.buffer.keys():
            if input in self.buffer[what].keys():
                return True
        return False

    def get(self, what, input=''):
        '''Get data from buffer for what(input).'''
        self.ensure_loaded()
        if not self.isbuffered(what, input):
            return None
        self.log.debug(f'Retrieved buffer {what}({input})')
        return deepcopy(self.buffer[what][input])

    def set(self, data, what, input=''):
        '''Set data to buffer for what(input).

        This will overwrite existing data.
        '''
        self.ensure_loaded()
        if what not in self.buffer.keys():
            self.buffer[what] = dict()
        self.buffer[what][input] = deepcopy(data)
        self.store()
        self.log.info(f'Buffered {what}({input})')

    def clear(self, what=''):
        self.ensure_loaded()
        if what in self.buffer:
            self.buffer[what] = dict()
        elif what:
            self.buffer = dict()
        self.store()

    def _get_bytestream(self) -> bytes:
        return pickle.dumps(self.buffer)

    def _set_bytestream(self, data: bytes):
        if data:
            self.buffer = pickle.loads(data)


def get_positional_arguments(func, *args, **kwargs):
    '''Resolve kwargs for default values.

    Note generic args or kwargs not being supported.
    '''
    argumentlist = func.__code__.co_varnames[0:(func.__code__.co_argcount)]
    default_value_list = func.__defaults__

    def getvalue(iarg, argname):
        '''Get value for single argument.'''
        # First, take the positional arguments by order:
        if iarg < len(args):
            return args[iarg]
        # Second, take remaining args either from the kwargs:
        if argname in kwargs:
            return kwargs[argname]
        # .. or from the corresponding default value
        else:
            nodefault_count = len(argumentlist) - len(default_value_list)
            # it is possible that the default value does not exist
            if iarg < nodefault_count:
                raise Exception(f'Function {func.__qualname__} must use '
                                f'{nodefault_count} parameters, '
                                f' only {len(args)} provided.')
            else:
                return default_value_list[iarg - nodefault_count]

    return tuple(
        getvalue(iarg, argname)
        for iarg, argname in enumerate(argumentlist)
    )


def buffered(buffer: Buffer | typing.Callable[..., Buffer]):
    '''Get decorator for buffering into user defined buffer.

    This function, taking the buffer as variable, returns the decorator.
    '''
    def _buffered(func):
        '''The decorator which will use buffer to wrap the function.'''
        if func.__kwdefaults__:
            raise Exception('kiss_cf cannot deal with default arguments for '
                            'kwargs. Check if you can use Buffer class '
                            'directly')

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            arglist = get_positional_arguments(func, *args, **kwargs)
            argstring = ','.join([str(arg) for arg in arglist])

            try:
                if isinstance(buffer, Buffer):
                    this_buffer = buffer
                elif callable(buffer):
                    this_buffer = buffer(*args, **kwargs)
            except Exception as e:
                log.exception(
                    'Buffer decorator must have either a buffer or a '
                    'function as input. The function must have the '
                    'same parameters like the decorated function and '
                    'it must return a buffer')
                raise e

            val = this_buffer.get(func.__name__, argstring)
            if val is None:
                val = func(*args, **kwargs)
                this_buffer.set(val, func.__name__, argstring)

            return val
        return wrapper

    return _buffered
