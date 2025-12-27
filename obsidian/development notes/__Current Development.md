Scope: GUI elements for nested GUI (including SettingSelect)

Status: SettingDict shows up in labeled frames and can be nested. Setting Select has fundamental concepts open.
* The base_setting does only know about the dict type, but not about a default format of the dict.
	* The SettingSelect would allow selecting from dicts with completely different content (contained types)
	* I suspect, there is currently ***no way to define the types of the dict elements*** for the base setting.
* When applying new values via select, since it assigns to a dict - different dict setups just extend the dict but do not reset it.
	* If current selection has a dict with "string A" and "int A", then selecting a second dict with "string B" and "int B" would result in having a value containing "string A", "int A", "string B" and "int B".
	* Resolving: check if applying to base setting can be done via set_state()
	* Add-on: the options of the base setting could be controlled which would a *define* what is possible to change for a setting select.
	* I guess a set_state() / get_state() is not available for ordinary settings since those are not storables.
* I currently try to use get_state()/set_state() to trigger utilizing the mutable settings of SettingDict.
	* This causes problems since the select_map only stores the values, not something equal to get_state() results.
	* **Alternative**: a setting dict should include similar options (mutable options)
		* Shouldn't the dict actually accept value settings which do not include all items *or* additional items?
	* **Actually wrong**: SettingSelect must ensure a clean state of the Setting before assigning values.
		* But if I clear all the settings in the dict, it would purge all options.


## Open Details
* (***accepted for now***) mixing normal seting and SettingDict looks awkward. Also a second level dict does not distinguish much from the first level dict since the frames are not indented in any way. >> A bordered label frame may need some padding around it. 
	* Placing a labeled frame is different from a non-labeled frame, in general?
	* Just placing a SettingDict (within Setting context) must be different?