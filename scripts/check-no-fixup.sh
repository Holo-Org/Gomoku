#!/usr/bin/env bash
# Pre-push hook: Reject temporary commits (fixup! and !)
#
# These commits are meant for local work only:
# - fixup! commits: Created by `git commit --fixup`, should be squashed
# - ! commits: Temporary work-in-progress, should be removed
#
# Usage: This script is called by git-hooks.nix during pre-push stage

set -e

# ANSI colors
RED='\033[91m'
YELLOW='\033[93m'
BOLD='\033[1m'
RESET='\033[0m'

# Read stdin for push info (required by git pre-push hook)
while read -r local_ref local_sha remote_ref remote_sha; do
    # Skip if deleting a branch
    if [ "$local_sha" = "0000000000000000000000000000000000000000" ]; then
        continue
    fi

    # Determine range of commits to check
    if [ "$remote_sha" = "0000000000000000000000000000000000000000" ]; then
        # New branch: check all commits reachable from local_sha
        RANGE="$local_sha"
    else
        # Existing branch: check only new commits
        RANGE="$remote_sha..$local_sha"
    fi

    # Search for forbidden commit patterns
    FORBIDDEN_COMMITS=$(git log --pretty=format:"%h %s" "$RANGE" 2>/dev/null | grep -E "^[a-f0-9]+ (fixup!|!)" || true)

    if [ -n "$FORBIDDEN_COMMITS" ]; then
        echo ""
        echo -e "${RED}${BOLD}ERROR: Cannot push temporary commits${RESET}"
        echo ""
        echo -e "${YELLOW}The following commits should be squashed before pushing:${RESET}"
        echo ""
        echo "$FORBIDDEN_COMMITS" | while read -r line; do
            echo "  $line"
        done
        echo ""
        echo "Use 'git rebase -i' to squash fixup! commits or remove ! commits."
        echo ""
        exit 1
    fi
done

exit 0
