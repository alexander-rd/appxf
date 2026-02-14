# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: Apache-2.0
'''Facade for APPXF gui module'''

# TODO: this module should be renamed closer to tkinter and may even be split
# off and planned as separate package to open up for other GUI integrations. If
# there will be a command line integration, this would be one staying in APPXF
# scope.

from .common import GridFrame, ButtonFrame, GridToplevel, GridTk, AppxfGuiError

from .setting_base import SettingFrameDefault
from .setting_select import SettingSelectFrame, SettingSelectDetailFrame
from .setting_dict import SettingDictColumnFrame, SettingDictSingleFrame, SettingDictWindow

from .application import AppxfApplication
from .config import ConfigMenu
from .login import Login
from .registration_user import RegistrationUser
from .registration_admin import RegistrationAdmin
