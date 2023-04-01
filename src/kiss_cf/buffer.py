from copy import deepcopy
import functools


class Buffer():
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

    # TODO: clarify storage:
    #
    # Name: The buffer is intended to be used for a domain of data. The domain
    # name assigned at initialization is used to persist the data buffer to
    # re-use it's content on the next application execution.

    def __init__(self):
        self.buffer = dict()

    def isbuffered(self, what: str, input: str):
        '''Check if what/input is buffered'''
        if what in self.buffer.keys():
            if input in self.buffer[what].keys():
                return True
        return False

    def get(self, what, input=''):
        '''Get data from buffer for what(input).'''
        if not self.isbuffered(what, input):
            # TODO: should we change to:
            # raise Exception(f'Buffer {self.name} does not contain {what}({input})')
            return None
        print(f'Retrieved buffer {what}({input})')
        return deepcopy(self.buffer[what][input])

    def set(self, data, what, input=''):
        '''Set data to buffer for what(input). This will overwrite existing
        data.
        '''
        if what not in self.buffer.keys():
            self.buffer[what] = dict()
        self.buffer[what][input] = deepcopy(data)
        print(f'Buffered {what}({input})')

    def clear(self, what=''):
        if what in self.buffer:
            self.buffer[what] = dict()
        elif what:
            self.buffer = dict()

    def persist(self):
        raise Exception("Not yet implemented!")


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


def buffered(buffer: Buffer):
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

            val = buffer.get(func.__name__, argstring)
            if val is None:
                val = func(*args, **kwargs)
                buffer.set(val, func.__name__, argstring)

            return val
        return wrapper

    return _buffered
