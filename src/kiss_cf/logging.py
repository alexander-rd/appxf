import logging as builtin_logging
import os
from . import fileversions

# Common usage will not like to include kiss_cf logging and python builtin
# logging.
logging = builtin_logging


def activate_logging(app_scope: str | None = None,
                     directory: str = './data',
                     n_files: int = 5):

    formatter = logging.Formatter(
            '%(asctime)s.%(msecs)03d '
            '%(levelname)s %(name)s.%(funcName)s(%(lineno)s): '
            '%(message)s',
            '%H:%M:%S')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    if not os.path.exists(directory):
        os.mkdir(directory)
    cleanup(directory, n_files)
    filename = fileversions.get_filename('logging_(yyyyMMdd)_(00).txt',
                                         directory=directory)
    filename = os.path.join(directory, filename)

    file_handler = logging.FileHandler(filename=filename, mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    kiss_logger = logging.getLogger('kiss_cf')
    kiss_logger.addHandler(console_handler)
    kiss_logger.addHandler(file_handler)
    kiss_logger.setLevel(logging.DEBUG)

    if app_scope is not None:
        app_logger = logging.getLogger(app_scope)
        app_logger.addHandler(console_handler)
        app_logger.addHandler(file_handler)
        app_logger.setLevel(logging.DEBUG)


def cleanup(directory: str, n_files: int = 5):
    print('--- CLEANUP ---')

    def is_relevant(file: str):
        return file.startswith('logging_') and file.endswith('.txt')
    files = filter(is_relevant, os.listdir(directory))
    files = [os.path.join(directory, f) for f in files]
    files.sort(key=lambda x: os.path.getmtime(x))
    for file in files[:-5]:
        os.remove(file)
    print(files)
