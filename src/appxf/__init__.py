# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
'''Facade for APPXF basic classes'''
# Basic classes exposed here shall only have dependencies to python builtin
# modules. This facade shall not expose any object from sub-modules. Rationale:
# using APPXF shall not enforce loading of unnecessary dependencies which are
# typically present in sub-modules.

from .options import Options
from .stateful import Stateful
