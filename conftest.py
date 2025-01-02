from appxf import logging


FLAG_LOG_ACTIVATED = False
def pytest_runtest_setup(item):
    global FLAG_LOG_ACTIVATED
    if not FLAG_LOG_ACTIVATED:
        logging.activate_logging('kiss_cf')
        FLAG_LOG_ACTIVATED = True
