from appxf import logging


FLAG_LOG_ACTIVATED = False
def pytest_runtest_setup(item):
    if not FLAG_LOG_ACTIVATED:
        logging.activate_logging('kiss_cf')
