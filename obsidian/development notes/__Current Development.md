**Goal:** Ensure user data and configuration data is protected during exchange (encryption)

**Steps**
1) Admin provides a file with **admin keys**. Those are just the **encryption** and **signing keys** to be entered into the user database. **Not encrypted.**
2) User loads the keys into his user database.
	1) set_admin_keys() already exists (??)
3) User provides **user data**  and **user keys** with **shared encryption for admins**. Signing does not yet make sense since it cannot be verified against a known bit of information.
4) Admin reads registration request and proceeds with registration.
5) Admin provides response encrypted for user and signed from admin. User can verify the signature based on the keys from steps (1) and (2)
