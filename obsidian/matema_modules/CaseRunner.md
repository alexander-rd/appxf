<!--Copyright 2026 the contributors of APPXF (github.com/alexander-rd/appxf)-->
<!--SPDX-License-Identifier: 0BSD-->
# Initialization Tree
* Doing nothing when: no command line arguments
* If command line arguments include any "process_*"
	* run the process (no file parsing required, this command should be at first place)
* If command line arguments include any matema commands (not yet defined)
	* parse commands
* Otherwise, arguments remain stored anyway and processing can wait until run()
*

* At run() or if there are command line arguments:
	* parse file and command line arguments
# Run Decision Tree
* Test file does not contain