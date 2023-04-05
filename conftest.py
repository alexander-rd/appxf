from kiss_cf import logging


def pytest_sessionstart(session):
    logging.activate_logging()
