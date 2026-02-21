<!--Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)-->
<!--SPDX-License-Identifier: 0BSD-->
# User Registry

Assume an application that shares information with others. How does the application know which *others* exist? How do those *others* get access to your data?

Via a user registration, you can **maintain users** and their **roles**. You can **securely provide credentials** to your users during the **registration process** and after registration any **data can be shared securely**.

Connected Use Cases:
* [[Registration]] is required to set up the user registry.
* [[Data Synchronization]] is enabled by having a user identity and roles defined

## FAQ
### How is the user registry updated?
If the admin removes a user or changes roles, the user registry will be uploaded to the remote location automatically. During startup of the application, as part of the user registration check, the user registry will be updated before this check.
### Can users rights be revoked?
You can remove a user. Without cleanup, the user-id will remain blocked. You can add or remove roles from a user. At least one role must remain. Access permissions will be forwarded accordingly. Please be aware of the [[Limitations|security limitations]].
### What happens if a user lost it's data?
If the application data is lost or corrupted, the user just needs to re-register with a fresh application. Shared data will be available again after registration. Since APPXF defines the user-id and the users public key as identification data, the user will get a *new* entry in the user registry.

A manual mapping to the old user ID is not supported since the added complexity does not seem to match the benefit.