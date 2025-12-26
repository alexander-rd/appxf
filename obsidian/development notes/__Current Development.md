Scope: GUI elements for nested GUI (including SettingSelect)

Status: SettingDict shows up in labeled frames and can be nested.
* mixing normal seting and SettingDict looks awkward. Also a second level dict does not distinguish much from the first level dict since the frames are not indented in any way. >> A bordered label frame may need some padding around it. 
	* Placing a labeled frame is different from a non-labeled frame, in general?
	* Just placing a SettingDict (within Setting context) must be different?