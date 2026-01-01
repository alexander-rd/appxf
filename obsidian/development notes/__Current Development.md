**Goal:** Ensure user data and configuration data is protected during exchange (encryption)

**Steps**
1) OK - Admin provides a file with **admin keys**. Those are just the **encryption** and **signing keys** to be entered into the user database. **Not encrypted.**
2) OK - User loads the keys into his user database.
	1) set_admin_keys() already exists (??)
3) OK - User provides **user data**  and **user keys** with **shared encryption for admins**. Signing does not yet make sense since it cannot be verified against a known bit of information.
4) OK - Admin reads registration request and proceeds with registration.
5) Admin provides response encrypted for user and signed from admin. User can verify the signature based on the keys from steps (1) and (2)
# Alternatives
## User Request
### UserRequest is handling encryption
* (-) UserRequest does not know the Security module, nor does it know the admin keys (from the user DB)
### Registry is handling encryption
* (+) It knows all the bits and pieces to do the encryption (Security, UserDB, ...)

# ToDo
* manual registration cycle test: it seems the app instance remains intact (registry object remains loaded) because the USER_DB is never generat
	* >> NO.. ..storing the USER_DB after admin key writing is missing. This was just not a problem up to now.
*  The key_blob_map in the custom processing in registry shall use use_id's instead of the public keys for which the keys were generated.
* User registration: if admin keys are not yet loaded, the keys to write the request (and load a response) should be grayed out.
* ?? Designated set of user information (setting dict with user ID, hidden keys,USER CONFIG and ROLES)
	* Roles is a multi select from the list of existing roles. That's a very specific extended setting.
	* The value is a list of strings? It is correct if items pop up only once, they are comma separated and they are contained in the maintained list.
	* Despite the default view with comma separated list, there would be a special view (multi columns) that allows ticking the values.
* registry.get_request() allows direct access to the user data and may even require knowledge of the UserRequest object. To ensure this data remains encrypted, registry should only expose the bytes.
	* But how does the GUI then access the data for display? The admin must be able to display user data from a request.
	* >> Registry allows to unpack a user request into a user entry that can be displayed. This will be a setting dict (USER ID + USER CONFIG + USER ROLES)
* If (like above) the requst_data interace cannot be protected, then at least the double-funciton get_request and get_request_data shall be unified.
* It's kind of the first time another instance is using security.hybrid_encrypt() as well as signing. I should review interface usage and "which module does what"
	* Security: only basic algorithm definitions
	* Registry: uses role based signature verification as well as hybrid encryption
	* SharedStorage: does the same as above together with Signature and PublicEncryption classes.
	* !! Public Encryption <-> Hybrid Encryption
	* !! Signing keys are often called "validation keys". If at all, they are "verification" keys.
		* signing (private) <-> verification (public)
		* encryption (public) <-> decryption (private)
		* >> For signign, the keys obtain specified names dependent on their function. for encryption, this is not the case.
* loading request/response raised errors - keep them an add messages OR other resolution
* add purging of USER_DB when loading admin keys
* USER_DB should never store() itself for efficiency reasons. This is safe since USER_DB is only private. Instead, registry has to manage stores after bulk operations.