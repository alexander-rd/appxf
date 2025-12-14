from appxf import logging
from kiss_cf.storage import Storage

FLAG_LOG_ACTIVATED = False
def pytest_runtest_setup(item):
    global FLAG_LOG_ACTIVATED
    if not FLAG_LOG_ACTIVATED:
        logging.activate_logging('kiss_cf', directory='.testing/log')
        FLAG_LOG_ACTIVATED = True

def pytest_runtest_teardown(item, nextitem):
    # need to reset storage context switching
    Storage.reset()

# Add logging for feature execution:
def pytest_bdd_before_step_call(request, feature, scenario, step, step_func):
    print(f"[BDD] {feature.filename}:{step.line_number} - {step.name}")
