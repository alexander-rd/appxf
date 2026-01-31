# ToDo
 * review drawio images (cleanup/remove)
 * Do I ship RemoteLocation_pycurl ???
 * Ticket to reconsider build support (checking out current main)
	 * I need this, but a future default must be based on a PyPi download
	 * Suggested: make it an OPTION to build against current mainline
	 * In appxf-demo repository, add the option to build against mainline (for release) and against pip install (normal usage) >> build_regression_test.yml and build.yml (maybe I can add subfolders?)
 * remove the .egg_info (where is this coming from??)
 * review documentation/MD files
 * scan comments in source files
 * Nasty thing when changing github actions: changes in the branch still pull reusable actions from main.
	 * How can this be done properly? The reusable actions are supposed to collect their actions from the mainline (or a valid tag).
 * Last things before merge:
	 * rename the last kiss_cf in the actions

# Others / Triage
* Create ticket  concerning FTP storage testing
	* Add another environment variable (if not present, testing will skip). Variable will be present upon GITHUB actions. And it will be assumed present if the dotenv file exist. (I do not want to set a variable every time I execute TOX)
* Create ticket: export coverage report. I want to have this somewhere readily available (for main)
* Create ticket to have a common APPXF error. Rationale is to be able to catch any APPXF expected exception (while not needing to know the specific one). This is relevant for testing but also to set expectations (which ones??)
* locale_scan and locale_update scripts needed source folder changes. Do I want to generalize this? Well, those scripts should actually become python to be usable directly from appxf (appxf_devtools together with build support)

* there was quite a problem that roles were not transferred correctly. I think the test cases did not cover this detail at all (right roles actually being received)
	* (1) Print roles during startup
	* (2) Add test case for registration cycle including roles transfer