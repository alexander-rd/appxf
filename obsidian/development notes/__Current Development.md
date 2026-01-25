* add something to user interface
	* Where?
		* Top level menu
		* Extension of CONFIG menu? >> Seems to be a good place, also for admin registration >> could be automated by plugging in the registry object into the config menu GUI element
* test
	* make test instructions scrollable
	* instance with ONE admin and TWO users (already existing)

# Journal
## Config Menu Addition
* Adding registry menu options to the config menu has one drawback:
	* Security and Registry must be loaded to determine admin roles
	* >> This is not really an issue since login and registration are currently checked *BEFORE* the main window is triggered
	* In use cases where the main window is available with some functions even without login, it will need some update() functionality to execute after a login.