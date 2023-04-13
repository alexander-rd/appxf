import logging as builtin_logging
import os
from . import fileversions

# Common usage will not like to include kiss_cf logging and python builtin
# logging.
logging = builtin_logging
getLogger = builtin_logging.getLogger


def activate_logging(app_scope: str | None = None,
                     directory: str = './data',
                     n_files: int = 5):
    ''' Activate logging for application

    It sets up logging to console and file logging (default: into
    ./data/log_yyyyMMdd_00.log). For kiss_cf and the scope of your application
    down to debug level, for the root logger only warning and info.

    It is assumed your application uses one root package and in it's
    __init__.py, you write:

    ```
    from kiss_cf import logging
    logging.activate_logging(__name__)
    ```

    Each module and class should then use it's own logger, like:

    ```
    from kiss_cf import logging
    log = logging.getLogger(__name__)
    ```

    Keyword Arguments:
        app_scope -- your application package (default: {None})
        directory -- directory to store the log files (default: {'./data'})
        n_files -- number of log files to retain (default: {5})
    '''

    file_formatter = logging.Formatter(
            '%(asctime)s.%(msecs)03d '
            '%(levelname)s %(name)s.%(funcName)s(%(lineno)s): '
            '%(message)s',
            '%H:%M:%S')
    console_formatter = logging.Formatter(
            '%(asctime)s.%(msecs)03d '
            '%(levelname)7s: '
            '%(message)s',
            '%H:%M:%S')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)

    if not os.path.exists(directory):
        os.mkdir(directory)
    cleanup(directory, n_files)
    filename = fileversions.get_filename('logging_(yyyyMMdd)_(00).log',
                                         directory=directory)
    filename = os.path.join(directory, filename)

    file_handler = logging.FileHandler(filename=filename, mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    logging.basicConfig(handlers=[console_handler, file_handler],
                        level=logging.WARN)

    kiss_logger = logging.getLogger('kiss_cf')
    kiss_logger.addHandler(console_handler)
    kiss_logger.addHandler(file_handler)
    kiss_logger.setLevel(logging.DEBUG)
    kiss_logger.propagate = False
    kiss_logger.debug('start logging')

    if app_scope is not None:
        app_logger = logging.getLogger(app_scope)
        app_logger.addHandler(console_handler)
        app_logger.addHandler(file_handler)
        app_logger.setLevel(logging.DEBUG)
        app_logger.propagate = False
        app_logger.debug('start logging')


def cleanup(directory: str, n_files: int = 5):
    ''' Cleanup log files

    This function is executed everytime you run activate_logging(). You should
    not need to call it yourself.

    Arguments:
        directory -- Directory of logging_*.log files

    Keyword Arguments:
        n_files -- _description_ (default: {5})
    '''
    def is_relevant(file: str):
        return file.startswith('logging_') and file.endswith('.log')
    files = filter(is_relevant, os.listdir(directory))
    files = [os.path.join(directory, f) for f in files]
    files.sort(key=lambda x: os.path.getmtime(x))
    for file in files[:-5]:
        os.remove(file)
