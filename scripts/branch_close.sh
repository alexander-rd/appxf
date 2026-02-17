#!/bin/bash
# Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: 0BSD

# branch_close.sh - Create or update a pull request for the current branch
#
# Usage: ./branch_close.sh
#
# This script:
# - Extracts the issue number from the current branch name
# - Fetches the issue title from GitHub
# - Creates or updates a pull request with:
#   - Title: The issue title
#   - Body: 'resolves #<issue-number>'
# - Displays a link to the pull request

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo '================================'
echo 'Verifying preconditions...'
"$SCRIPT_DIR/_verify_clean_working_tree.sh"

echo '================================'
echo 'Preparing pull request...'
echo '--------------------------------'

# Get current branch name
CURRENT_BRANCH=$(git branch --show-current)
DEFAULT_BRANCH="main"

if [ -z "$CURRENT_BRANCH" ]; then
    echo 'Error: Not currently on a branch'
    exit 1
fi

# Check if on default branch
if [ "$CURRENT_BRANCH" = "$DEFAULT_BRANCH" ]; then
    echo "Error: Cannot create PR from default branch ($DEFAULT_BRANCH)"
    echo 'Please switch to a feature branch first'
    exit 1
fi

echo "Current branch: $CURRENT_BRANCH"

# Extract issue number from branch name (assumes format: number_rest_of_name or
# number-rest-of-name)
ISSUE_NUMBER=$(echo "$CURRENT_BRANCH" | grep -oE '^[0-9]+')

if [ -z "$ISSUE_NUMBER" ]; then
    echo 'Error: Branch name must start with an issue number'
    echo 'Example: 42_implement_feature'
    echo "Current branch: $CURRENT_BRANCH"
    exit 1
fi

echo "Issue number: #$ISSUE_NUMBER"
echo '--------------------------------'

# Fetch issue details
echo "Fetching issue details for #$ISSUE_NUMBER..."
if ! gh issue view "$ISSUE_NUMBER" --json title,body &> /dev/null; then
    echo "ERROR: Could not fetch issue details for #$ISSUE_NUMBER"
    echo "If GitHub CLI (gh) is not installed:"
    echo "  sudo apt get install gh"
    echo "If you are not authorized:"
    echo "  Generate token: https://github.com/settings/tokens"
    echo "  Authenticate: gh auth login --with-token < your_token_file"
    echo "Make sure the issue exists and you have access to it."
    echo "  https://github.com/alexander-nbg/appxf/issues/$ISSUE_NUMBER"
    exit 1
fi

ISSUE_TITLE=$(gh issue view "$ISSUE_NUMBER" --json title --jq '.title')
ISSUE_URL=$(gh issue view "$ISSUE_NUMBER" --json url --jq '.url')

echo "Issue title: $ISSUE_TITLE"
echo "Issue URL: $ISSUE_URL"
echo '--------------------------------'

# Prepare PR body
PR_BODY="resolves #${ISSUE_NUMBER}"

# Check if PR already exists for this branch
echo 'Checking for existing pull request...'
EXISTING_PR=$(gh pr list --head "$CURRENT_BRANCH" --json number --jq '.[0].number' 2>/dev/null || echo '')

if [ -n "$EXISTING_PR" ]; then
    echo "Updating existing pull request #$EXISTING_PR..."

    # Update the PR
    if ! PR_EDIT_OUTPUT=$(gh pr edit "$EXISTING_PR" \
        --title "$ISSUE_TITLE" \
        --body "$PR_BODY" 2>&1); then
        echo 'ERROR: Failed to update pull request:'
        echo "$PR_EDIT_OUTPUT"
        exit 1
    fi

    PR_URL=$(gh pr view "$EXISTING_PR" --json url --jq '.url')

    echo '✓ Pull request updated successfully!'
    echo "PR #$EXISTING_PR: $ISSUE_TITLE"
    echo "URL: $PR_URL"
    echo '================================'
else
    echo 'Creating new pull request...'

    # Create the PR
    if ! PR_CREATE_OUTPUT=$(gh pr create \
        --title "$ISSUE_TITLE" \
        --body "$PR_BODY" \
        --base "$DEFAULT_BRANCH" 2>&1); then
        echo 'ERROR: Failed to create pull request:'
        echo "$PR_CREATE_OUTPUT"
        exit 1
    fi

    # Extract URL from output (gh pr create prints the URL)
    PR_URL=$(echo "$PR_CREATE_OUTPUT" | grep -oE 'https://github.com/[^[:space:]]+')

    echo '✓ Pull request created'
    echo "Title: $ISSUE_TITLE"
    echo "URL: $PR_URL"
    echo '================================'
fi

echo ''
echo 'Next steps:'
echo '  - Review the PR: '"$PR_URL"
echo '  - Request reviewers if needed: gh pr edit --add-reviewer <username>'
echo ''
