#!/usr/bin/env python3
"""
Commit Message Convention Checker

This script validates commit messages against the project's commit convention:

    scope: message

Rules:
    - Format: `scope: message` (lowercase scope, colon, space, message)
    - Message must start with a verb in imperative present tense (e.g., "add", "fix")
    - Maximum 72 characters total
    - No trailing punctuation (period, exclamation, etc.)
    - Scope should be from the known list (warning if not, but allowed)

Special cases (bypass validation):
    - Commits starting with `fixup!` (for interactive rebasing)
    - Commits starting with `!` (temporary commits for squashing)

Usage:
    check-commit-msg.py <commit-message-file>
    check-commit-msg.py --message "scope: add feature"

Exit codes:
    0 - Valid commit message
    1 - Invalid commit message
"""

import sys
import re
import argparse
from pathlib import Path


# =============================================================================
# CONFIGURATION
# =============================================================================

# Maximum length for commit message (first line)
MAX_LENGTH = 72

# Known/recommended scopes for this project
# If a scope is not in this list, a warning is shown but commit is allowed
KNOWN_SCOPES = [
    "ai",        # AI algorithm (minimax, alpha-beta, move ordering)
    "board",     # Board representation and game logic
    "eval",      # Evaluation function and pattern detection
    "protocol",  # Protocol handling and communication
    "main",      # Main entry point and CLI
    "nix",       # Nix flake and development environment
    "scripts",   # Scripts (hooks, utilities)
    "docs",      # Documentation (README, comments)
    "test",      # Tests
    "ci",        # Continuous integration
    "deps",      # Dependencies
    "refactor",  # Code refactoring (no functional change)
    "style",     # Code style and formatting
    "perf",      # Performance improvements
    "fix",       # Bug fixes (can also be used as scope)
    "feat",      # New features (can also be used as scope)
    "chore",     # Maintenance tasks
]

# Trailing characters that should not end a commit message
FORBIDDEN_TRAILING = ".!?;:,"


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def is_bypass_commit(message: str) -> bool:
    """
    Check if the commit message should bypass validation.

    Bypass commits:
    - `fixup! ...` - For interactive rebasing (git commit --fixup)
    - `! ...` - Temporary commits for squashing

    Args:
        message: The commit message (first line).

    Returns:
        True if validation should be bypassed.
    """
    return message.startswith("fixup!") or message.startswith("!")


def parse_commit_message(message: str) -> tuple[str | None, str | None]:
    """
    Parse a commit message into scope and message parts.

    Expected format: `scope: message`

    Args:
        message: The commit message (first line).

    Returns:
        Tuple of (scope, message_body), or (None, None) if parsing fails.
    """
    # Pattern: word (scope), colon, space, rest (message)
    pattern = r"^([a-z][a-z0-9_-]*): (.+)$"
    match = re.match(pattern, message)

    if match:
        return match.group(1), match.group(2)
    return None, None


def check_imperative_verb(message_body: str) -> tuple[bool, str]:
    """
    Check if the message starts with an imperative verb.

    Args:
        message_body: The message part (after scope:).

    Returns:
        Tuple of (is_valid, first_word).
    """
    words = message_body.split()
    if not words:
        return False, ""

    if words[0] != words[0].lower():
        return False, words[0].lower()

    first_word = words[0].lower()

    # Common imperative verbs that end with 's' (not third person)
    IMPERATIVE_S_EXCEPTIONS = {
        "pass", "process", "ress", "class", "less", "miss",
        "stress", "press", "cross", "focus", "discuss"
    }

    # Heuristic checks for likely non-imperative forms
    if first_word.endswith("ed"):  # Past tense: "added", "fixed"
        return False, first_word[:-2]
    if first_word.endswith("ing"):  # Gerund: "adding", "fixing"
        return False, first_word[:-4] if first_word.endswith("tting") else first_word[:-3] # "getting" -> "get"
    if (first_word.endswith("s") and len(first_word) > 2
        and first_word not in IMPERATIVE_S_EXCEPTIONS):  # Third person: "adds", "fixes"
        return False, first_word[:-1]

    return True, first_word


def validate_commit_message(message: str) -> tuple[bool, list[str], list[str]]:
    """
    Validate a commit message against the project convention.

    Args:
        message: The commit message (first line only).

    Returns:
        Tuple of (is_valid, errors, warnings).
        - is_valid: True if the commit should be allowed
        - errors: List of error messages (commit will be rejected)
        - warnings: List of warning messages (commit allowed but noted)
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Get first line only
    first_line = message.splitlines()[0]

    # Check for bypass commits
    if is_bypass_commit(first_line):
        return True, [], ["Bypass commit detected (fixup!/!), skipping validation"]

    # Check length
    if len(first_line) > MAX_LENGTH:
        errors.append(
            f"Commit message too long: {len(first_line)} chars (max {MAX_LENGTH})"
        )

    # Check trailing punctuation
    if first_line and first_line.strip()[-1] in FORBIDDEN_TRAILING:
        errors.append(
            f"Commit message should not end with '{first_line.strip()[-1]}'"
        )

    # Parse scope and message
    scope, message_body = parse_commit_message(first_line)

    if scope is None or message_body is None:
        errors.append(
            "Invalid format. Expected: `scope: message`\n"
            "  Example: `ai: add alpha-beta pruning`"
        )
        return False, errors, warnings

    if message_body != message_body.strip():
        errors.append("The commit message contains trailing/leading whitespaces")

    if "  " in message_body:
        errors.append("The commit contains doubled spaces")

    # Check scope
    if scope not in KNOWN_SCOPES:
        warnings.append(
            f"Unknown scope '{scope}'. Known scopes: {', '.join(sorted(KNOWN_SCOPES))}"
        )

    # Check imperative verb
    is_imperative, first_word = check_imperative_verb(message_body)

    if not is_imperative:
        if first_word.endswith("ed"):
            suggestion = first_word[:-2]
            errors.append(
                f"Use imperative mood: '{first_word}' -> '{suggestion}'\n"
                f"  Write 'add feature' not 'added feature'"
            )
        elif first_word.endswith("ing"):
            suggestion = first_word[:-3]
            if suggestion.endswith("t") or suggestion.endswith("n"):
                suggestion = suggestion[:-1]  # "getting" -> "get"
            errors.append(
                f"Use imperative mood: '{first_word}' -> '{suggestion}'\n"
                f"  Write 'add feature' not 'adding feature'"
            )
        elif first_word.endswith("s"):
            suggestion = first_word[:-1]
            errors.append(
                f"Use imperative mood: '{first_word}' -> '{suggestion}'\n"
                f"  Write 'add feature' not 'adds feature'"
            )
        if first_word:
            errors.append(
                f"Use imperative mood: '{message_body.split()[0]}' -> '{first_word}'\n"
            )
        else:
            errors.append(
                f"Message should start with an imperative verb (e.g., add, fix, update)"
            )

    # Check that message body is not empty after the verb
    words = message_body.split()
    if len(words) < 2:
        errors.append("Message body is empty")

    return len(errors) == 0, errors, warnings


# =============================================================================
# OUTPUT FORMATTING
# =============================================================================

# ANSI color codes
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_error(message: str) -> None:
    """Print an error message in red."""
    print(f"{RED}{BOLD}ERROR:{RESET} {RED}{message}{RESET}", file=sys.stderr)


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    print(f"{YELLOW}{BOLD}WARNING:{RESET} {YELLOW}{message}{RESET}", file=sys.stderr)


def print_success(message: str) -> None:
    """Print a success message in green."""
    print(f"{GREEN}{BOLD}OK:{RESET} {GREEN}{message}{RESET}", file=sys.stderr)


# def print_help_hint() -> None:
#     """Print a hint about the expected commit format."""
#     print(file=sys.stderr)
#     print(f"{BOLD}Expected format:{RESET} scope: message", file=sys.stderr)
#     print(file=sys.stderr)
#     print(f"{BOLD}Rules:{RESET}", file=sys.stderr)
#     print("  - scope: lowercase identifier (e.g., ai, board, docs)", file=sys.stderr)
#     print("  - message: starts with imperative verb (e.g., add, fix, update)", file=sys.stderr)
#     print("  - max 72 characters", file=sys.stderr)
#     print("  - no trailing punctuation", file=sys.stderr)
#     print(file=sys.stderr)
#     print(f"{BOLD}Examples:{RESET}", file=sys.stderr)
#     print("  ai: add alpha-beta pruning optimization", file=sys.stderr)
#     print("  docs: update README with installation instructions", file=sys.stderr)
#     print("  fix: resolve edge case in win detection", file=sys.stderr)


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 for valid, 1 for invalid).
    """
    parser = argparse.ArgumentParser(
        description="Validate commit message against project convention"
    )
    parser.add_argument(
        "commit_msg_file",
        nargs="?",
        help="Path to file containing commit message (e.g., .git/COMMIT_EDITMSG)"
    )
    parser.add_argument(
        "--message", "-m",
        help="Commit message string (for testing)"
    )

    args = parser.parse_args()

    # Get commit message
    if args.message:
        commit_message = args.message
    elif args.commit_msg_file:
        try:
            commit_message = Path(args.commit_msg_file).read_text()
        except FileNotFoundError:
            print_error(f"File not found: {args.commit_msg_file}")
            return 1
        except IOError as e:
            print_error(f"Cannot read file: {e}")
            return 1
    else:
        parser.print_help()
        return 1

    # Validate
    is_valid, errors, warnings = validate_commit_message(commit_message)

    # Print results
    for warning in warnings:
        print_warning(warning)
    for error in errors:
        print_error(error)
    return not is_valid


if __name__ == "__main__":
    sys.exit(main())
