#!/bin/bash
# Copyright 2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: 0BSD

# _verify_clean_working_tree.sh - Verify the working tree being clean and up to
# date
#
# This script is used as a precondition check in other scripts (e.g.
# branch_start.sh, branch_close.sh)
#
# Exits with error code 1 if:
# - Working tree is not clean (uncommitted changes)
# - Branch is not up to date with origin

set -e

echo '--[git status]------------------'
STATUS_OUTPUT=$(git status)
echo "$STATUS_OUTPUT"
echo '--------------------------------'

# Check for clean working tree
if ! echo "$STATUS_OUTPUT" | grep -q 'nothing to commit, working tree clean'; then
    echo 'Error: Working tree is not clean. Please commit and push your changes first.'
    exit 1
fi

# Check if branch is up to date
if ! echo "$STATUS_OUTPUT" | grep -q 'Your branch is up to date'; then
    echo 'Error: Branch is not up to date with origin. Please pull and/or push your changes first.'
    exit 1
fi

echo '✓ Repository is clean and up to date'
