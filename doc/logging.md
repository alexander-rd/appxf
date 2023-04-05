Logging
=======

Feature Outline
---------------

Logging during development shows progress and hints you left in your messages.
Anything you issue with `Logging.log(LEVEL, 'message')` will continue to be
__printed to the console (1)__. When your application is shipped out of your
hands, you rely on __logging written to a file (2)__.

The above features are switched on by default for any kiss_cf feature (while you could switch it off). In the application, you only need to use the folllowing instead of print which by default logs on INFO level:

```python
from kiss_cf.logging import log

# ... some of your code ...
log('Processing awesomness started ...')
# ... some of your code ...
```

Note that some of your logging is relevant as feedback to the user, like:
 "Password is too short" or "Process finished OK". For this, you can embedd a
__logging frame (3)__. This will show a single line with the latest info
message __showing progress (3a)__ and __showing the latest INFO message (3b)__. Because you will sometimes need to allow the user accessing more lines of such logging (like for: "Process finished with 4 warnings (see above)") the logging frame can __extend to 5 lines of scrollable log lines (4)__.


```python
from kiss_cf.logging.gui import LoggingFrame
# ... other code that generates your gui
log_frame = LoggingFrame(parent)
# you still need to place the frame via, e.g., grid()
```

Note that kiss_cf uses the python standard logging module (TBD: how to access)
but simplifies usage by the the following assumptions:
 * **Active by default.** You need to deactivate it if you don't like to use it
   when using kiss_cf.
 * **Preconfigured.** To simplify usage, you do not need to configure anything.
 * **Static.** You even do not need to create an object. kiss_cf comes with a
   static instance that is used by default.

Of course, you can change the configuration and you probably (not tested) can
even generate multiple kiss_cf Logging objects.

Pop-Up-Messages
---------------

No feature is provided here to link pop up warnings/errors with logging. Just forward the message also to the kiss_cf logging module.

Extentions
----------

 * Sending bug report via Email. Automatically sends all available log files.
 * Catch exceptions by default to logging module and stream to logging before
   throwing (an Exception configuration or already built in?)