# Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
'''PyInstaller hook registration
'''
from PyInstaller.utils.hooks import collect_data_files

# Add translation mo files to resources:
datas = collect_data_files(
    package='appxf',
    includes=['locale/*/LC_MESSAGES/*.mo'])
