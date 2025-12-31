**Goal:** Ensure user data and configuration data is protected during exchange (encryption)

**Steps**
1) Admin provides a file with **admin keys**. Those are just the **encryption** and **signing keys** to be entered into the user database. **Not encrypted.**
2) User loads the keys into his user database.
	1) set_admin_keys() already exists (??)
3) User provides **user data**  and **user keys** with **shared encryption for admins**. Signing does not yet make sense since it cannot be verified against a known bit of information.
4) Admin reads registration request and proceeds with registration.
5) Admin provides response encrypted for user and signed from admin. User can verify the signature based on the keys from steps (1) and (2)

# Alternatives
## User Request
### UserRequest is handling encryption
* (-) UserRequest does not know the Security module, nor does it know the admin keys (from the user DB)
### Registry is handling encryption
* (+) It knows all the bits and pieces to do the encryption (Security, UserDB, ...)

# ToDo
* User registration: if admin keys are not yet loaded, the keys to write the request (and load a response) should be grayed out.
* registry.get_request() allows direct access to the user data and may even require knowledge of the UserRequest object. To ensure this data remains encrypted, registry should only expose the bytes.
	* But how does the GUI then access the data for display? The admin must be able to display user data from a request.
	* >> Registry allows to unpack a user request into a user entry that can be displayed. This will be a setting dict (USER ID + USER CONFIG + USER ROLES)
* If (like above) the requst_data interace cannot be protected, then at least the double-funciton get_request and get_request_data shall be unified.
* Check external usage of `registry._user_db` registry has to provide interfaces to avoid this access.