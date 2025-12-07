## Basic Logging
Logging during development shows progress and hints you left in your messages. Any log you issue will be __printed to the console__. When your application is shipped out of your hands, you rely on __logging written to a file__. Once log files are written, some __log rotation and cleanup of storage would be nice__: kiss_cf starts a new log file for each application session (log rotation) and will only keep the last five log files (cleanup).

Assumption is that your application structures code into one top-level package. The \_\_init\_\_.py of this top-level package is the place to activate logging: 
```python
from appxf import logging

logging.activate_logging(__name__)
```

The function __activate_logging()__ must only be called once within your application.

Each module from which you want to log will then use: 
```python
from appxf import logging

log = logging.getLogger(__name__)
```

Note that __getLogger()__ is the same __getLogger()__ from python's logging module such that all logging functions from there apply. The above __log__ would be used like:
```python
def some_function():

log.debug('')
log.info('For state changes')
log.warning('Unexpected but OK')
log.error('Definitely wrong but you can fail safely')
```
and produce log lines like the following, the number (12) being the code line in the module:
```
09:56:40.407 INFO app_package.module.some_function(12): For state changes
```
Note that date is part of the file name (`./data/logging_yyyyMMdd_00.log`) and, therefore, not printed.

## Logging Classes
If you are working with classes, you likely want to have the class name contained in the log lines. In this case, you can setup logging like:
```python
from appxf import logging


class YourClass():
	log = logging.getLogger(__name__ + '.YourClass')
```

## Logging Other Modules
Warnings and Errors of other modules are logged to console and file just like logs of kiss_cf and your application. What would be missing is uncought exceptions. For that reason, you should embed your main code into:
 ```python
from appxf import logging

import your_application

log = logging.getLogger(__name__)

try:
	# your main application code, like:
	your_application.run()
except Exception:
	log.exception('Uncought exception.')
```

Note the logger __log__ in your main file is NOT in the scope of your application package and will only log WARNING level or above. It's scope will be \_\_main\_\_.

## Logging GUI command errors (tkinter)
If you are running a tkinter GUI, your command callbacks might throw exceptions which tkinter only prints to stderr by default. To change this behavior, you need to add this bit to your main application.
```python
# ... wherever you start your main GUI ...
gui_root = tkinter.Tk()
# This line replaces the default behavior with the function below
gui_root.report_callback_exception = _handle_gui_exception

def _handle_gui_exception(exception, value, traceback):
	log.exception("GUI callback with exception:")
```

## Logging to GUI (not yet implemented)
Some of your logging is relevant as feedback to the user, like: "Password is too short" or "Process finished OK". For this, you can embed a __logging frame__. This will show a single line with the latest info message __showing progress__ and __showing the latest INFO message__. Because you will sometimes need to allow the user accessing more lines of such logging (like for: "Process finished with 4 warnings (see above)") the logging frame can __extend to 5 lines of scrollable log lines__.
```python
from appxf.logging.gui import LoggingFrame

# ... other code that generates your gui

log_frame = LoggingFrame(parent)

# you still need to place the frame via, e.g., grid()
```

## Pop-Up-Messages
No feature is provided here to link pop up warnings/errors with logging. Just forward the message also to the kiss_cf logging module.

## Extentions (not yet implemented) 
* Sending bug report via Email. Automatically sends all available log files.