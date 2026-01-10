# Gomoku AI Algorithm Documentation

## Protocol Support

### Mandatory Commands (Fully Implemented)

| Command | Description |
| ------- | ----------- |
| `START [size]` | Initialize board of given size |
| `TURN X,Y` | Process opponent's move, respond with our move |
| `BEGIN` | Play first move on empty board |
| `BOARD` ... `DONE` | Load board state, then play |
| `INFO key value` | Receive game settings |
| `END` | Terminate the program |

### Optional Commands (Implemented)

| Command | Description |
| ------- | ----------- |
| `ABOUT` | Return brain metadata |
| `RESTART` | Reset board for new game |
| `TAKEBACK X,Y` | Undo a move |

### INFO Keys Supported

- `timeout_turn` - Time limit per move (ms)
- `timeout_match` - Total time limit (ms)
- `time_left` - Remaining match time (ms)
- `max_memory` - Memory limit (bytes)
- `game_type` - 0=human, 1=brain, 2=tournament
- `rule` - Game rule bitmask
- `folder` - Folder for persistent files

## AI Algorithm

### Minimax with Alpha-Beta Pruning

The AI uses the Minimax algorithm, which explores the game tree assuming optimal play from both sides:

1. **Maximizing nodes** (AI's turn): Choose the move with the highest score
2. **Minimizing nodes** (opponent's turn): Choose the move with the lowest score
3. **Leaf nodes**: Evaluate using the heuristic function

**Alpha-beta pruning** eliminates branches that cannot affect the final decision, significantly reducing the search space.

### Heuristic Evaluation

The evaluation function recognizes these patterns:

| Pattern | Description | Score |
| ------- | ----------- | ----- |
| Five | 5+ in a row (win) | 1,000,000 |
| Open Four | 4 stones, both ends open | 50,000 |
| Closed Four | 4 stones, one end open | 10,000 |
| Open Three | 3 stones, both ends open | 5,000 |
| Closed Three | 3 stones, one end open | 500 |
| Open Two | 2 stones, both ends open | 100 |
| Closed Two | 2 stones, one end open | 10 |

Opponent patterns are weighted with a defense multiplier (0.9x).

### Move Generation

To reduce the search space, the AI only considers moves within 2 cells of existing stones. This is based on the observation that good Gomoku moves are almost always near existing stones.

### Move Ordering (Optional)

Two move ordering implementations are available in `src/ai.py`:

1. **Simple (default)**: No ordering, faster per call
2. **With ordering**: Sorts moves by preliminary evaluation, more pruning

To switch implementations, uncomment/comment the appropriate `get_candidate_moves` function in `src/ai.py`.

## Configuration

### Command-Line Arguments

| Argument | Description | Default |
| -------- | ----------- | ------- |
| `--debug` | Enable debug output to stderr | Disabled |
| `--depth N` | Set Minimax search depth | 4 |

### Tunable Parameters

In `src/ai.py`:

- `DEFAULT_DEPTH`: Default search depth (4)
- `CANDIDATE_RADIUS`: Distance from stones to consider (2)

In `src/evaluation.py`:

- `SCORES`: Pattern score values
- `DEFENSE_MULTIPLIER`: Weight for opponent patterns (0.9)
