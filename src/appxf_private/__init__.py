# Facade for private APPXF basic classes
#
# Basic classes exposed here shall only have dependencies to python builtin
# modules. This facade shall not expose any object from sub-modules. Rationale:
# using APPXF shall not enforce loading of unnecessary dependencies which are
# typically present in sub-modules.

from .stateful import Stateful
from .options import Options
