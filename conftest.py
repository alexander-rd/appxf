# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
from appxf import logging
from appxf.storage import Storage

FLAG_LOG_ACTIVATED = False
def pytest_runtest_setup(item):
    global FLAG_LOG_ACTIVATED
    if not FLAG_LOG_ACTIVATED:
        logging.activate_logging('appxf', directory='./.testing')
        FLAG_LOG_ACTIVATED = True

def pytest_runtest_teardown(item, nextitem):
    # need to reset storage context switching
    Storage.reset()

# Add logging for feature execution:
def pytest_bdd_before_step_call(request, feature, scenario, step, step_func):
    print(f"[BDD] {feature.filename}:{step.line_number} - {step.name}")
