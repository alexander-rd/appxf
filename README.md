# Basic Cross-Functionals (BCF)

This toolbox covers cross functional concerns like configuration settings,
persisting data, logging or security to limit the effort writing a simple
application. It is created to provide customizations on top of
[OpenOlitor](https://openolitor.org/), a web tool for community aided
agriculture (CSA). Hence, the naming of the toolbox and a module to easily get
data from this database.

Solutions to cross-functional concerns have strong impact on non-functional
requirements or vice versa. To allow a quick decion on whether this code might
help you and to guide it's development, a list of nun-functional requirements.
 * Usability (?): interfaces shall be simple.

[security](doc/security.md)

Cross-Cutting Concerns
======================

 * Configuration
 * Logging
 * Persisting Data
 * Data Exchange via FTP
 * Security
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