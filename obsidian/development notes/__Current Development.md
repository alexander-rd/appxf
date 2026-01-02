**Goal:** Ensure user data and configuration data is protected during exchange (encryption)

**Steps**
1) OK - Admin provides a file with **admin keys**. Those are just the **encryption** and **signing keys** to be entered into the user database. **Not encrypted.**
2) OK - User loads the keys into his user database.
	1) set_admin_keys() already exists (??)
3) OK - User provides **user data**  and **user keys** with **shared encryption for admins**. Signing does not yet make sense since it cannot be verified against a known bit of information.
4) OK - Admin reads registration request and proceeds with registration.
5) OK - Admin provides response encrypted for user and signed from admin. User can verify the signature based on the keys from steps (1) and (2)
# ToDo
* User registration: if admin keys are not yet loaded, the keys to write the request (and load a response) should be grayed out.
* ?? Designated set of user information (setting dict with user ID, hidden keys,USER CONFIG and ROLES)
	* Roles is a multi select from the list of existing roles. That's a very specific extended setting.
	* The value is a list of strings? It is correct if items pop up only once, they are comma separated and they are contained in the maintained list.
	* Despite the default view with comma separated list, there would be a special view (multi columns) that allows ticking the values.
* registry.get_request() allows direct access to the user data and may even require knowledge of the UserRequest object. To ensure this data remains encrypted, registry should only expose the bytes.
	* But how does the GUI then access the data for display? The admin must be able to display user data from a request.
	* >> Registry allows to unpack a user request into a user entry that can be displayed. This will be a setting dict (USER ID + USER CONFIG + USER ROLES)
* If (like above) the requst_data interace cannot be protected, then at least the double-funciton get_request and get_request_data shall be unified.
* loading request/response raised errors - keep them an add messages OR other resolution
* **add purging of USER_DB** when loading admin keys
* I think, there is no need to provide the maintained KEYS from registry to anywhere.. ..registry supports signature verification and hybrid encryption.. ..so, no need for the keys to leave the registry.
* GENERAL REVIEW of registry

Tickets:
* Data should be signed before encryption as a general rule of thumb.
	* To flatten the data structures, I would embed the signature as fixed bytes into the data bytes to render: "data-bytes + signature -> structure -> pack to bytes" into "new_bytes = data-bytes + signature-bytes"
	* Affects: SharedStorage, Registry registration response
	* Includes a second look at the file structure for shared storage and must consider the use cases for purging users from the user databse.
