# ToDo
 * review drawio images (cleanup/remove)
 * Do I ship RemoteLocation_pycurl ???
 * Ticket to reconsider build support (checking out current main)
	 * I need this, but a future default must be based on a PyPi download
	 * Suggested: make it an OPTION to build against current mainline
	 * In appxf-demo repository, add the option to build against mainline (for release) and against pip install (normal usage) >> build_regression_test.yml and build.yml (maybe I can add subfolders?)
 * remove the .egg_info (where is this coming from??)

# Others / Triage
* locale_scan and locale_update scripts needed source folder changes. Do I want to generalize this? Well, those scripts should actually become python to be usable directly from appxf (appxf_devtools together with build support)

* there was quite a problem that roles were not transferred correctly. I think the test cases did not cover this detail at all (right roles actually being received)
	* (1) Print roles during startup
	* (2) Add test case for registration cycle including roles transfer