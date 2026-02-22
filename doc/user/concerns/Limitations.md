<!--Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)-->
<!--SPDX-License-Identifier: 0BSD-->
# Security Limitations

## Credentials
APPXF does not expose credentials in the logging and does only expose it to admins if configured properly. But to be able to access services, users do have passwords! Theoretically, they could alter the code or rebuild the application to extract them.
### Status Quo
Without APPXF, if credentials must be shared, they will be shared. They will be available to others with the same limitation as stated above. But will the exchange channel be secure? Will the password be updated frequently?
APPXF, at least, secures the communication path *and* makes rolling out updated passwords seamless.
### Alternatives
APPXF is a solution for small-scale groups providing a minimum of security. The only way to properly protect credentials is by not providing direct access. A typical way to achieve this is a web service where users log in and the server handles the credentials. Such web based services will typically be too much effort for small-scale groups might not be safer, if:
* there are vulnerabilities in the web service including all it's exposed interfaces like the login procedure.
* there are vulnerabilities of the hosting server.
### Mitigation
* Check if you need to share the credentials. Share only with the roles that really need it.
* Update passwords frequently, with APPXF you have a secure and convenient way to update them.
## Data
APPXF can share information securely to a selected group of users and even retract this access again. However, users had once access to the data and could have copied that data already before retraction of access rights. They could also omit any update by remaining offline and alter the application or built a new one to keep the data access.
### Status Quo
Without APPXF, data would still be shared including the risk of users not removing the data upon request.
### Alternatives
At the point you needed to share data, you cannot fully control on how it will be used.
### Mitigation
* Consider what data you need to share.
	* Consider the roles that need access.
	* Consider if a role needs access to all data or only part of it.
* Consider APPXF options. While you can use APPXF to just exchange a file that is directly readable, you can also model the same information within the application. Corresponding application data files will only be readable by the application itself. While the application could be altered or rebuild, it will be considerably more effort to keep information readable.
## Conclusions
You are responsible for the security of the data you are handling. You need to assess the sensitivity of your data and the attack surface you are providing. Check the following:
1. Do you really have to exchange sensible data?
2. If you need to exchange sensible data, is your solution acceptable?
