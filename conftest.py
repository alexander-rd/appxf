from appxf import logging


def pytest_sessionstart(session):
    logging.activate_logging()
