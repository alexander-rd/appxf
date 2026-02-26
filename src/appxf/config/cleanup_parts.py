# Copyright 2024-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0

# TODO: reactivate storing and loading sections as INI files


import configparser


class ToolConfigParser(configparser.ConfigParser):
    '''Internal helper with predefined settings for ConfigParser()'''

    def __init__(self, **kwargs):
        # Note that we need to change the comment prefix to something else and
        # allow "no values" to keep them as keys without values. Other
        # functions must then ignore the "#" keys.
        super().__init__(comment_prefixes='/', allow_no_value=True, **kwargs)
        self.optionxform = str
