# Requirements
* The manual test case must be executable directly without any test management.
	* The script may still use any helpers
	* For manual execution, the following is optional:
		* test case description
		* collection of results
	* Any automatic reporting or step automation shall still be available.
* The MaTeMa shall collect test case results and maintain them within a database

# Design Alternatives
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