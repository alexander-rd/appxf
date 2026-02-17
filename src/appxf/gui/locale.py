# Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
'''Translation setup for APPXF GUI modules
'''
import gettext
import importlib.resources

# Translation setup. No language is defined in translation() to apply the
# system language by default.
_translation = gettext.translation(
    domain='appxf-gui',
    localedir=str(importlib.resources.files("appxf") / "locale"),
    fallback=True)

# Export the pgettext function as _ for context-aware translations
_ = _translation.pgettext
# Also export other useful translation functions if needed
ngettext = _translation.ngettext
