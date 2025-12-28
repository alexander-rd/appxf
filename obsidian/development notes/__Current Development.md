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

```
# TODO: How can I deal with input like above where the values are set by
# providing tuples (could also be setting objects).. ..which is valid but fails
# since this will always generate new setting objects within the maintaines
# base_setting.
#
# Possible solution: stripping the select map to "values, only". For
# dictionaries, this would imply:
# 1) take a COPY of the base_setting (get_state() and set_state() to empty
# ??)
# 2) apply the select item to this COPY
# 3) use copy.value to get the values for the select_map
#
# I'm not happy about the COPY in step (1) above but adding an item must never
# change the current value for a SettingSelect.
#
# Using get_state()/set_state() from SettingSelect sounds risky wince the
# structure (particularly options) may be different.
# >> Settings must provide a get_copy() operator.
#
# Could I also use a deepcopy?? Yes, this should work also.
```