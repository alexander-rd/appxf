# Requirements
* The manual test case must be executable directly without any test management.
	* The script may still use any helpers
	* For manual execution, the following is optional:
		* test case description
		* collection of results
	* Any automatic reporting or step automation shall still be available.
* The MaTeMa shall collect test case results and maintain them within a database
* A manual test case shall not use any command line arguments. Rationale: the test case helper and the MaTeMa may utilize this interface and conflicts may arise.
# Design Decisions

## Multiple Tk Windows
**Problem Core.** A test execution helper which is used during the manual test case will collect test case results and may spawn instances for the application under test. The test helper is a Tk instance and any application is a Tk instance while one process should only have ***one Tk instance in one thread***. (The MaTeMa instance is not relevant since it already spawns the manual test case in a separate process).
### Normal Manual Test Case Execution
* python script construct objects and fills the test helper
* some `run()` is called from the test helper based on the ***objects*** created in the test script
### Test Cases with Tk instances
Neither can the Tk instance of the application under test be launched nor can the test helper launch an already generated object. Reason: the test helper itself is a Tk instance. Hence, the following applies:
* the test instance ***wraps***:
	* setup and teardown code
	* code for spawning the Tk instances
* the test helper will check command line arguments to the test case
* if command line arguments are empty, it will initiate the helper window and:
	1. identify the module it is called from
	2. read the case documentation
	3. read provided action symbols (e.g. functions with particular naming pattern)
	4. add buttons for each action symbol including the method to execute: calling the test case file with a command line argument indicating the function
* if the command line arguments are not empty, it will:
	1. just execute the method that was indicated by the command line argument
The command line argument will have a particular pattern such that command line arguments can be used as further interface from the MaTeMa to the test execution helper.

## Ownership of Case Execution
### Script is responsible
The Script would contain the helper that launches the test case execution. This helper would display the case description, collect results and allow automated stimulation via a buttons.
* (-) Efforts for the MaTeMa to collect the test case results after execution.
	* Most likely via the file system and a configurable `.matema` folder.
* (-) Strong requirement to the manual test case implementation: it has to provide the case results.
	* If case results are not available, the MaTeMa can only evaluate the process exist status.
* (+) Automation or convenience actions (buttons) are self contained and available via manual execution
* (/) There are typically three windows: 
	* the MaTeMa
	* an execution helper for case description and results collection
	* the UI that is tested
### The MaTeMa is responsible
The MaTeMa reads case descriptions from the python file and displays them. It also collects the case results.
* (+) Automation steps must still be provided by the script itself leading also to three windows as in "script is responsible". Only if this is not required, the MaTeMa can switch it's view to the case execution, avoiding one of the three windows.
* (+) The MaTeMa directly collects the tester evaluation text.
* (!) If the MaTeMa process calls the manual test, static variables would be shared! Hence, the manual test must still be launched as a subprocess.
	* (-) As a consequence, the MaTeMa cannot gather anything from the case execution
### Conlcusions
* MaTeMa being responsible does not *fully* resolve conveying information from the case execution to the test manager.
* A **case result provider** should be separated from the **case execution helper** such that existing case executions can use the **case result provider** at the end to convey execution results. The **execution helper** would include the **result provider**.