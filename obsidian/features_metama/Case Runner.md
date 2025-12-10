The CaseRunner class is instantiated at the end of you manual test case. The simplest form looks like:
```python
'''
Test case __description__ that can apply mardown.
'''
from appxf_metama import CaseRunner

# implementation of your manual test case

CaseRunner()
```
When the test case is called via the MaTeMa as a subprocess, it uses **command line arguments** which are parsed by case runner. For this reason, to avoid conflicts, your manual test case ***must not*** use command line arguments to avoid conflicts.

The overhead to your existing manual test case comprises: loading additional dependencies and parsing the command line via CaseRunner().

#TODO The CaseRunner currently does not restrict it's actions to just command line reading. There is no feature to ***not*** start the file parsing. The examples already draft expected behavior.
# Recommendations
## Single Instance
Split startup() and teardown() code. This has two effects:
* this code is not increasing your coverage, the case runner will start coverage only for the execution of test()
* because of the above, you limit the file dependencies to the test case and avoid marking the case invalid due to changes in the corresponding files
```python
'''
Test case __description__ that can apply mardown.
'''
from appxf_metama import CaseRunner

# construct any objects you need

def setup():
	# any preparations before test execution
	
def teardown():
	# any steps after test execution
	
def test():
	# implementation of your test case

CaseRunner().run()
```
The functions setup() and teardown() are executed before and after every call of test() or process_\*() 
## Sandboxed Instances
Applications often have a persisted state on the file system (or on a server), referenced as sandbox. To prepare and tear down this sandbox, use the following hooks:
```python
def sandbox_setup():
	# sandbox preparation executed ONCE before any setup()
	
def sandbox_teardown():
	# sandbox teardown executed ONCE before the case runner 
	# closes and after any teardown()
```
## Multiple Instances
If you are testing multiple instances or want to be able to close and reopen your instance during testing, define corresponding "process_" functions. The CaseRunner will add buttons to the execution window using the function summary as labels. Upon button press, a new process is spawned, the module is loaded and the code from your process_() is executed.
```python	
def process_app_admin():
	''' Admin Application '''
	
def process_app_user():
	''' User Application '''
```
