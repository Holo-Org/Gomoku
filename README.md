# Gomoku AI - Azemoku

A Gomoku (Five in a Row) AI bot implementing the Minimax algorithm with alpha-beta pruning. Compatible with the [liskvork](https://git.sr.ht/~emneo/liskvork) game manager and the standard Gomoku AI protocol.

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Overview

Azemoku is a Gomoku AI brain designed for the Epitech G-AIA-500 project. It plays Gomoku (also known as Five in a Row, Wuzi Qi, or Gobang) by communicating with a game manager through standard input/output using the Gomoku AI protocol.

**Features:**

- Compliant with the standard Gomoku AI protocol

## Requirements

- **Python 3.11** or higher
- No external dependencies (standard library only)

### Using Nix (Recommended)

If you have Nix with flakes enabled:

```bash
# Enter development shell
nix develop

# Or run directly
nix run
```

### Without Nix

Ensure Python 3.11+ is installed:

```bash
python3 --version  # Should be 3.11 or higher
```

## Installation

1. Clone or download this repository
2. Ensure the main script is executable:

```bash
chmod +x pbrain-gomoku-ai
```

3. (Optional) Generate Nix flake lock file:

```bash
nix flake update
```

## Usage

### Running the Bot

The bot communicates via stdin/stdout. For testing, you can run it directly:

```bash
./pbrain-gomoku-ai
```

### With liskvork Game Manager

1. Download [liskvork](https://releases.liskvork.org/liskvork/) for your platform
2. Configure liskvork to use this bot:

```bash
liskvork --brain1 ./pbrain-gomoku-ai --brain2 <other-brain>
```

### Manual Testing

You can test the bot manually by typing commands:

```Raw
START 20
OK
BEGIN
10,10
TURN 10,11
9,10
END
```

## Technical Constraints

Per the project specification:

- **Time limit**: 5 seconds per move
- **Memory limit**: 70 MB
- **Board size**: 20x20 (standard)
- **Rules**: Freestyle (exactly 5 not required)
- **Libraries**: Standard library only (no TensorFlow, scikit-learn, etc.)

## License

This project is created for educational purposes as part of the Epitech curriculum.

---

**Author**: Renaud Manet, Kylian Chandelier, Tom Feldkamp
**Version**: 1.0.0
**Tournament Name**: Azemoku
