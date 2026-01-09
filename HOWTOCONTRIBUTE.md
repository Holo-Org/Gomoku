# How to Contribute

## Project Structure

```Raw
gomoku/
├── pbrain-gomoku-ai     # Main executable (Python script)
├── flake.nix            # Nix flakes configuration
├── flake.lock           # Nix lock file (generated)
├── ruff.toml            # Ruff linter/formatter configuration
├── mypy.ini             # Mypy type checker configuration
├── .brawl               # Tournament registration ("Azemoku")
├── README.md            # Project overview and instructions
├── HOWTOCONTRIBUTE.md   # Contribution guidelines (this file)
├── scripts/
│   ├── check-commit-msg.py  # Commit message validator
│   └── check-no-fixup.sh    # Pre-push hook (rejects fixup!/!)
└── src/
    ├── ALGORITHM.md     # AI algorithm documentation
    ├── __init__.py      # Package initialization
    ├── main.py          # Entry point, CLI argument parsing
    ├── board.py         # Board representation, game logic
    ├── evaluation.py    # Heuristic evaluation, pattern detection
    ├── ai.py            # Minimax, alpha-beta, move ordering
    └── protocol.py      # Protocol command handling
```

### Module Descriptions

- **board.py**: Defines the `Board` class with stone placement, win detection, and board operations.
- **evaluation.py**: Pattern recognition and scoring. Analyzes lines for consecutive stones and classifies patterns.
- **ai.py**: Implements Minimax with alpha-beta pruning. Contains both simple and ordered move generation.
- **protocol.py**: Parses protocol commands and manages game state. Bridges between manager and AI.
- **main.py**: Entry point with argument parsing and main loop.

## Development

### Setting Up the Environment

Using Nix (recommended):

```bash
# Enter development shell (installs hooks automatically)
nix develop
```

Using direnv (for automatic shell activation):

```bash
# Create .envrc file
echo "use flake" > .envrc

# Allow direnv to load it
direnv allow
```

With direnv, the development environment activates automatically when you `cd` into the project directory.

This will:

- Set up Python 3.11+ environment
- Install ruff (linter/formatter) and mypy (type checker)
- Install git hooks for code quality and commit conventions

### Code Quality Tools

The project enforces strict code quality through:

| Tool | Purpose | Command |
| ---- | ------- | ------- |
| `ruff format` | Code formatting | `ruff format .` |
| `ruff check` | Linting | `ruff check .` or `ruff check --fix .` |
| `mypy` | Type checking | `mypy --strict src/` |

All Python code must have type annotations (enforced by mypy in strict mode).

### Git Hooks

Git hooks are managed by [git-hooks.nix](https://github.com/cachix/git-hooks.nix) and automatically installed when entering `nix develop`:

| Hook | Stage | Action |
| ---- | ----- | ------ |
| `ruff-format` | pre-commit | Checks code formatting |
| `ruff` | pre-commit | Runs linter |
| `mypy` | pre-commit | Runs type checker (strict mode) |
| `commit-msg` | commit-msg | Validates commit message format |
| `no-fixup-push` | pre-push | Rejects `fixup!` and `!` commits |

### Commit Convention

All commits must follow this format:

```Raw
scope: message
```

**Rules:**

- **scope**: Lowercase identifier (see list below)
- **message**: Starts with imperative verb (add, fix, update, remove, etc.)
- **length**: Maximum 72 characters
- **punctuation**: No trailing period or punctuation

**Valid scopes:**
`ai`, `board`, `eval`, `protocol`, `main`, `nix`, `scripts`, `docs`, `test`, `ci`, `deps`, `refactor`, `style`, `perf`, `fix`, `feat`, `chore`

**Examples:**

```Shell
# Good
ai: add alpha-beta pruning optimization
docs: update README with installation guide
fix: resolve edge case in win detection
refactor: simplify pattern matching logic

# Bad
ai: Added new feature           # Past tense
ai: adding new feature          # Gerund
ai: add new feature.            # Trailing period
AI: add feature                 # Uppercase scope
```

**Special commits (for local work only):**

- `fixup! <original message>` - For `git commit --fixup` (squash later)
- `! WIP message` - Temporary commits (remove before push)

These bypass validation but are rejected by the pre-push hook.

### Testing Manually

```bash
# Start the bot in debug mode
./pbrain-gomoku-ai --debug

# Type commands:
START 20
BEGIN
TURN 9,9
# etc.
```

### Debug Output

Debug output goes to stderr (won't interfere with protocol):

```bash
./pbrain-gomoku-ai --debug 2>debug.log
```

### Enabling Move Ordering

Edit `src/ai.py` and swap the commented function:

1. Comment out the simple `get_candidate_moves` function
2. Uncomment the ordered version below it
3. Save and run

### Brawl Tournament

The `.brawl` file registers the bot as "Azemoku" for the Epitech tournament. The file is automatically detected when pushed to the repository.

Tournament website: https://gomoku.epitest.eu
