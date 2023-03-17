# KISS Cross-Functionals (kiss_cf)

This toolbox covers cross functional concerns like configuration, persisting
data, logging or security to limit the effort writing simple applications.

Solutions to cross-functional concerns have strong impact on non-functional
requirements or vice versa. The following list was compiled to allow a quick
decion on whether this toolbox is for you and to guide it's development.
Provided numbers only provide a rough idea.
 * The toolbox aims for **easy application creation**. This includes simple to use
   interfaces and the need for documentation and examples.
   * Not however that time is limited and support is appreciated. Contact me!
 * Supported are **desktop applications** that are **shared with a limited number of
   people** (like: 50).
   * Not suited for online applications.
   * Might not scale well to 1000 or more users.
 * **Data exchange** with other instances is based on one or few (like 3) people
   having writing rights while more (like 50) are just consuming the results.
   * See security section: you essentially give away your email or database
     passwords to the people with writing rights.
 * **Update frequency** is expected like 20 times a week and rare (once a month)
   peak reading are 150 times/h.
   * Methods provided to exchange data are not suited for continuous data
     exchange between instances.
 * **Keep it simple, stupid** (KISS) is part of the name for a reason. This
   toolbox tries not to go fancy.
   * Developers might still fall in the trap adding less usefull stuff. Sorry.

Cross-Cutting Concerns
======================

 * Configuration
 * Logging
 * Persisting Data
 * Data Exchange via FTP
 * [Security](doc/security.md)
 * GUI
 * Extention modules
   * Email sending
   * Email inbox parsing
   * OpenOlitor database connection

Persistency
-----------

Storing data locally is currently incorporated into configuration and security
modules. If this toolbox is used, the following default locations apply where
modules place files:
 * security: ./data/security
 * config: ./data/config
Where "./" is the location of the binary.

Language
--------

All implementation is in (American) English. When components have user visible
strings, they will offer an option **language** that expects a dictionary
mapping from the visible English strings into what you need.

In cases of mapping to an existing database
([OpenOlitor](https://www.docarit.ch/PDFs/openlitor_schema.svg)) field names
from that database are maintained.

OpenOlitor Database Connection
------------------------------

[OpenOlitor](https://openolitor.org/) is a web tool for community aided
agriculture (CSA). An application to support processes in an CSA was the
originating trigger for this toolbox.
