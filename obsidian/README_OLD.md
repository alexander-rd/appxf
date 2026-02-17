<!--Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)-->
<!--SPDX-License-Identifier: 0BSD-->
This is the old README that was present in the original private repository. It needs to be merged into the new README and planned documentation.
# APPXF

This toolbox covers cross functional concerns like configuration, persisting
data, logging or security to limit the effort writing simple applications.

Solutions to cross-functional concerns have strong impact on non-functional
requirements or vice versa. The following list was compiled to allow a quick
decision on whether this toolbox is for you and to guide it's development.
Provided numbers only provide a rough idea.
 * The toolbox aims for **easy application creation**. This includes simple to use
   interfaces and the need for documentation and examples.
   * Apparently, time is limited. Support is appreciated. Contact me.
 * Supported are **desktop applications** that are **shared with a limited number of
   people** (like: 50).
   * Not suited for online applications.
   * Does not aim to scale for 1000 or more users.
 * **Data exchange** with other instances is based on one or few (like 3) people
   having writing rights while more (like 50) are just consuming the results.
	 * See security section: you essentially give away your email or database passwords to the people with writing rights.
	 * **Update frequency** is expected like 20 times a week and rare (once a month) peak reading are 150 times/h.
	 * Methods provided to exchange data are not suited for continuous data exchange between instances.

Cross-Cutting Concerns
======================

 * Configuration
 * [Logging](doc/logging.md)
 * Persisting Data
 * Data Exchange via FTP
   * Note to be added: installation of libcurl requires libssl-dev
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

GUI
---

The decision to be made: tkinter or QT. Since the APPXF framework does not aim
for professionals, a quick learning curve is essential such that tkinter was
chosen as the basis (see also:
[pythonguis.com](https://www.pythonguis.com/faq/pyqt-vs-tkinter/)). [Tkinter
Designer](https://github.com/ParthJadhav/Tkinter-Designer) and
[Figma](https://www.figma.com/de/) or [VisualTK](https://visualtk.com/) might
help with GUI design. [PySimpleGUI](https://www.pysimplegui.org/en/latest/)
crossed me late for unknown reasons. I will reconsider for this even simpler
approach.

Language
--------

All implementation is in (American) English. When components have user visible
strings, they will offer an option **language** that expects a dictionary
mapping from the visible English strings into what you need.

In cases of mapping to an existing database
([OpenOlitor](https://www.docarit.ch/PDFs/openlitor_schema.svg)) field names
from that database are maintained.