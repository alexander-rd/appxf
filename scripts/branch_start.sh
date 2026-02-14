#!/bin/bash
# Copyright 2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: 0BSD

# branch_start.sh - Create a new branch and display associated APPXF issue information
#
# Usage: ./branch_start.sh <branch_name>
# Example: ./branch_start.sh 42_implement_feature
#
# The branch name should start with an issue number (e.g., 42_implement_feature)

set -e

if [ $# -eq 0 ]; then
    echo 'Error: Branch name is required'
    echo 'Example: ./branch_start.sh 42_implement_feature'
    exit 1
fi

BRANCH_NAME="$1"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo '================================'
echo 'Verifying preconditions...'

"$SCRIPT_DIR/_verify_clean_working_tree.sh"

# Extract issue number from branch name (assumes format: number-rest-of-name)
ISSUE_NUMBER=$(echo "$BRANCH_NAME" | grep -oE '^[0-9]+')

if [ -z "$ISSUE_NUMBER" ]; then
    echo 'Error: Branch name must start with an issue number'
    echo 'Example: 42-implement-feature'
    exit 1
fi

echo "--------------------------------"
echo "Details of issue #$ISSUE_NUMBER"

# Try to fetch issue details using GitHub CLI
if gh issue view "$ISSUE_NUMBER" --json title,body &> /dev/null; then
    ISSUE_TITLE=$(gh issue view "$ISSUE_NUMBER" --json title --jq '.title')
    ISSUE_BODY=$(gh issue view "$ISSUE_NUMBER" --json body --jq '.body')

    echo "Title: $ISSUE_TITLE"
    echo ""
    echo "Summary:"
    echo "$ISSUE_BODY" | head -20

    # Show URL for full details
    ISSUE_URL=$(gh issue view "$ISSUE_NUMBER" --json url --jq '.url')
    echo ""
    echo "Full details: $ISSUE_URL"
    echo "================================"
else
    echo "WARNING: Could not fetch issue details for #$ISSUE_NUMBER"
    echo "If GitHub CLI (gh) is not installed:"
    echo "  sudo apt get install gh"
    echo "If you are not authorized:"
    echo "  Generate token: https://github.com/settings/tokens"
    echo "  Authenticate: gh auth login --with-token < your_token_file"
    echo "Make sure the issue exists and you have access to it."
    echo "  https://github.com/alexander-rd/appxf/issues/$ISSUE_NUMBER"
    echo "================================"
fi
echo "Press Enter to continue (or <Ctrl+C> to cancel)..."
read -r

echo "================================"
echo "Creating branch: $BRANCH_NAME"
echo "--------------------------------"

# Create the branch
git checkout -b "$BRANCH_NAME"
# Push to origin
git push -u origin "$BRANCH_NAME"

echo ""
echo "================================"
echo "Done."
