# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
from functools import cached_property
import subprocess

class GitInfo:
    def __init__(self):
        # nothing to init
        pass

    @cached_property
    def user_name(self):
        try:
            name = subprocess.check_output(
                ["git", "config", "user.name"],
                text=True).strip()
        except subprocess.CalledProcessError:
            name = 'Unknown GIT User'
        return name

    @cached_property
    def user_email(self):
        try:
            email = subprocess.check_output(
                ["git", "config", "user.email"],
                text=True).strip()
        except subprocess.CalledProcessError:
            email = 'Unknown GIT Email'
        return email