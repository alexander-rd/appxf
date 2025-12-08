''' User Registry :: Registration Request

__Situation:__ The user already logged in into the application but did not yet
register AND did not yet generate a registration request.

__Scope:__ Validate the generation of the registration request. You may store
it anywhere on your file system.
'''
from appxf_matema.case_runner import ManualCaseRunner
from tests._fixtures import test_sandbox

tester = ManualCaseRunner(__doc__)

test_sandbox.init_test_sandbox_for_caller_module()

# running currently requires a window or frame to run.. ..work in progress.
# tester.run()
