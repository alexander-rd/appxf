# KISS Cross-Functionals (kiss_cf)

![Test Linux](  https://github.com/alexander-rd/kiss_cf/actions/workflows/test-self-linux.yml/badge.svg)
![Test Windows](https://github.com/alexander-rd/kiss_cf/actions/workflows/test-self-win.yml/badge.svg)

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
   toolbox tries not to go too fancy.
   * The developer (me) might still fall in the trap adding less usefull stuff.
     Sorry. It's a bit like some management picking slogans on things they are
     not good at.

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

The decision to be made: tkinter or QT. Since the KISS framework does not aim
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

OpenOlitor Database Connection
------------------------------

[OpenOlitor](https://openolitor.org/) is a web tool for community aided
agriculture (CSA). An application to support processes in an CSA was the
originating trigger for this toolbox. kiss_cf makes it a bit easier to retrieve
data from the mariaDB that is used there.

See [this link to setup python](
https://mariadb.com/de/resources/blog/how-to-connect-python-programs-to-mariadb/)
and [this one for the API](
https://mariadb-corporation.github.io/mariadb-connector-python/index.html).

Developer Documentation
=======================

* [Test Strategy](doc/TestStrategy.md)