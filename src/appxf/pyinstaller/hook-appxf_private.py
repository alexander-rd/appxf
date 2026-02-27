# Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
"""PyInstaller hook registration"""
# ignoring "hook-*" naming convention (required by PyInstaller):
# ruff: noqa: N999

from PyInstaller.utils.hooks import collect_data_files

# Add translation mo files to resources:
datas = collect_data_files(package="appxf", includes=["locale/*/LC_MESSAGES/*.mo"])
