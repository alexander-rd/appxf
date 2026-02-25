# Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
'''Support for pyinstaller based builds'''


import os


def get_hook_dirs():
    '''Return this directory containing PyInstaller hooks

    This function is called by PyInstaller when it discovers the entry point
    registered in pyproject.toml under [project.entry-points.pyinstaller40].

    See also:
    https://pyinstaller.org/en/stable/hooks.html#providing-pyinstaller-hooks-with-your-package
    '''
    return [os.path.dirname(__file__)]
