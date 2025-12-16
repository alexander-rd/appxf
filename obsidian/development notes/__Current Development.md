### Configuration transfer via REGISTRY (SDT #14, Kiss #26)
**Status:** mechanism works to transfer configuration data via registration
response to the registering user. A drafted GUI is available, exposing required actions.

**Missing:** Validating test case and cleanup

**Observation.** While adding the GUI behavior it becomes apparent that the functional analysis in problem domain is missing. It appears in questions like: "what if the user needs to raise a new registration requests to repair something in the configuration (utilizing the registration config transfer)" or "what if the user was already registered - should there be an option to generate a response for an existing user". >> I should start adding some diagram on this level (and resolve the drawio ones).

## Observations
* I do not like the pop-up windows upon errors. However, errors should be treated. Adding some visibility must be a logging capabilty (log to file AND display pop up or into a logging stream)
* Gray out or leave empty the user information (and role assignment) until the request is loaded
* proper usage of "setup()" and "setup_sandbox()"

## Not yet considered
* **Shared storage**: even though it kind of works (for user DB share), conflicts must be handled before going live. Idea almost implies that the sync needs a plugin UI which is reversed dependency compared to Login and Registry.
* **User information** is not yet stored in user DB.  I don't even have a concept defined on how to maintain this efficiently. This information is not only exchanged between user and one/many admins.. ..it may also be available (read-only) for other users of the application (same role or all roles). >> #32
* **Encryption** of request/response >> #31