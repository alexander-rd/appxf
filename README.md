# OpenOlitorToolbox

This toolbox covers cross functional concerns like configuration settings,
persisting data, data exchange between instances or security to limit the
efforts writing a simple application. It was created to provide customizations
on top of [OpenOlitor](https://openolitor.org/), a web tool for community aided
agriculture (CSA). Hence, the naming of the toolbox and a module to easily get
data from this database.

[security](doc/security.md)

Language
--------

All implementation is in (American) English. When components have user visible
strings, they will offer an option **language** that expects a dictionary
mapping from the visible English strings into what you need.

In cases of mapping to an existing database
([OpenOlitor](https://www.docarit.ch/PDFs/openlitor_schema.svg)) field names
from that database are maintained.