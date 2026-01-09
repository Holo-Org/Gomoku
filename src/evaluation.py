"""
Evaluation module for Gomoku AI.

This module provides heuristic evaluation functions for the Gomoku board.
The evaluation is based on pattern recognition, identifying sequences of
stones and their potential to form winning lines.

=== PATTERN TERMINOLOGY ===

In Gomoku, patterns are classified by:
1. Length: Number of consecutive stones (2, 3, 4, or 5)
2. Openness: Whether the ends are blocked or open

Types of patterns:
- "Open" (or "Live"): Both ends are empty, can extend in either direction
- "Half-open" (or "Closed"): One end is blocked (by opponent or board edge)
- "Closed": Both ends are blocked (dead pattern, cannot win)

=== PATTERN VALUES ===

The scoring is based on threat level:
- Five in a row (WIN): Immediate victory
- Open Four: Guaranteed win next turn (opponent cannot block both ends)
- Closed Four: Must be blocked or we win
- Open Three: Creates open four next turn (very dangerous)
- Closed Three: Can become closed four
- Open Two: Building potential
- Closed Two: Minor potential

The scores are exponentially increasing because:
1. Higher patterns are exponentially more threatening
2. This ensures the AI prioritizes immediate threats over long-term potential
"""

from src.board import DIRECTIONS, Board, Cell

# =============================================================================
# SCORING CONSTANTS
# =============================================================================

# Winning score (higher than any sum of other patterns)
SCORE_WIN = 1_000_000

# Pattern scores for the AI (maximizing player)
# These values are carefully tuned to ensure proper prioritization:
# - An open four should be valued higher than multiple open threes
# - Defensive moves (blocking opponent) should be valued appropriately
SCORES = {
    "five": SCORE_WIN,  # Winning pattern
    "open_four": 50_000,  # Guaranteed win (opponent can't block both ends)
    "closed_four": 10_000,  # Must be blocked
    "open_three": 5_000,  # Creates open four if not blocked
    "closed_three": 500,  # Can become closed four
    "open_two": 100,  # Building potential
    "closed_two": 10,  # Minor potential
}

# Multiplier for opponent patterns (defense is slightly less important than offense)
# But blocking an opponent's open four is still critical
DEFENSE_MULTIPLIER = 0.9


# =============================================================================
# PATTERN DETECTION
# =============================================================================


def analyze_line(board: Board, row: int, col: int, dr: int, dc: int, player: int) -> dict[str, int]:
    """
    Analyze a line through a position for patterns.

    This function examines a line passing through (row, col) in the direction
    (dr, dc) and its opposite (-dr, -dc). It counts:
    - Consecutive stones of the player
    - Empty spaces at each end
    - Whether ends are blocked by opponent or board edge

    Args:
        board: The game board.
        row: Row of the center position.
        col: Column of the center position.
        dr: Row direction component.
        dc: Column direction component.
        player: The player whose patterns to analyze.

    Returns:
        Dictionary containing:
        - 'count': Number of consecutive stones
        - 'open_ends': Number of open ends (0, 1, or 2)
        - 'space_before': Empty spaces before the sequence
        - 'space_after': Empty spaces after the sequence
    """
    # Count consecutive stones in positive direction
    count = 1  # Start with the stone at (row, col) if it exists

    # If the center position is empty, we're analyzing potential moves
    if board.get_cell(row, col) != player:
        count = 0

    # Scan in positive direction (dr, dc)
    r, c = row + dr, col + dc
    while board.is_valid_position(r, c) and board.get_cell(r, c) == player:
        count += 1
        r += dr
        c += dc

    # Check what's at the end (positive direction)
    end_positive = board.get_cell(r, c)
    open_positive = end_positive == Cell.EMPTY

    # Scan in negative direction (-dr, -dc)
    r, c = row - dr, col - dc
    while board.is_valid_position(r, c) and board.get_cell(r, c) == player:
        count += 1
        r -= dr
        c -= dc

    # Check what's at the end (negative direction)
    end_negative = board.get_cell(r, c)
    open_negative = end_negative == Cell.EMPTY

    # Count open ends
    open_ends = int(open_positive) + int(open_negative)

    return {
        "count": count,
        "open_ends": open_ends,
    }


def classify_pattern(count: int, open_ends: int) -> str | None:
    """
    Classify a pattern based on stone count and open ends.

    This function takes the analysis from analyze_line() and determines
    what type of pattern it represents.

    Args:
        count: Number of consecutive stones.
        open_ends: Number of open ends (0, 1, or 2).

    Returns:
        Pattern name ('five', 'open_four', etc.) or None if not significant.

    Pattern Classification:
    ========================

    Five (5+ stones):
        XXXXX -> Winning pattern

    Open Four (4 stones, 2 open ends):
        .XXXX. -> Opponent cannot block both ends, guaranteed win

    Closed Four (4 stones, 1 open end):
        OXXXX. or .XXXXO -> Must be blocked or loses

    Open Three (3 stones, 2 open ends):
        .XXX. -> Can become open four

    Closed Three (3 stones, 1 open end):
        OXXX. or .XXXO -> Can become closed four

    Open Two (2 stones, 2 open ends):
        .XX. -> Building potential

    Closed Two (2 stones, 1 open end):
        OXX. or .XXO -> Minor potential
    """
    if count >= 5:
        return "five"

    if count == 4:
        if open_ends == 2:
            return "open_four"
        if open_ends == 1:
            return "closed_four"
        # If open_ends == 0, the four is dead (blocked both ends)

    if count == 3:
        if open_ends == 2:
            return "open_three"
        if open_ends == 1:
            return "closed_three"

    if count == 2:
        if open_ends == 2:
            return "open_two"
        if open_ends == 1:
            return "closed_two"

    return None


def count_patterns(board: Board, player: int) -> dict[str, int]:
    """
    Count all patterns for a player on the board.

    This function scans the entire board and counts occurrences of each
    pattern type for the specified player.

    Args:
        board: The game board.
        player: The player to analyze (Cell.OWN or Cell.OPPONENT).

    Returns:
        Dictionary mapping pattern names to their counts.

    Implementation Note:
    ====================
    To avoid counting the same pattern multiple times (once for each stone
    in the pattern), we only count patterns starting from specific positions.
    We iterate through the board and only count patterns where the current
    position is the "start" of the pattern (leftmost or topmost stone).
    """
    patterns = {
        "five": 0,
        "open_four": 0,
        "closed_four": 0,
        "open_three": 0,
        "closed_three": 0,
        "open_two": 0,
        "closed_two": 0,
    }

    # Track which patterns we've already counted to avoid duplicates
    # We use a set of (start_row, start_col, direction_index) tuples
    counted: set[tuple[int, int, int]] = set()

    for row in range(board.size):
        for col in range(board.size):
            if board.get_cell(row, col) != player:
                continue

            for dir_idx, (dr, dc) in enumerate(DIRECTIONS):
                # Check if this is the start of a pattern
                # (the cell before in this direction is not the same player)
                prev_r, prev_c = row - dr, col - dc
                is_valid = board.is_valid_position(prev_r, prev_c)
                if is_valid and board.get_cell(prev_r, prev_c) == player:
                    # Not the start of the pattern, skip to avoid double counting
                    continue

                # Create a unique key for this pattern
                pattern_key = (row, col, dir_idx)
                if pattern_key in counted:
                    continue
                counted.add(pattern_key)

                # Analyze the pattern in this direction
                analysis = analyze_line(board, row, col, dr, dc, player)
                pattern_type = classify_pattern(analysis["count"], analysis["open_ends"])

                if pattern_type is not None:
                    patterns[pattern_type] += 1

    return patterns


# =============================================================================
# BOARD EVALUATION
# =============================================================================


def evaluate_board(board: Board) -> int:
    """
    Evaluate the board state and return a score.

    Positive scores favor OWN (the AI), negative scores favor OPPONENT.
    The magnitude indicates how advantageous the position is.

    Args:
        board: The game board to evaluate.

    Returns:
        Integer score. Positive = good for AI, negative = good for opponent.

    Evaluation Strategy:
    ====================

    1. First check for immediate wins (five in a row)
    2. Count all patterns for both players
    3. Sum up weighted pattern scores
    4. Apply defense multiplier to opponent patterns

    The evaluation considers both offensive potential (our patterns)
    and defensive necessity (opponent's patterns).
    """
    # Count patterns for both players
    own_patterns = count_patterns(board, Cell.OWN)
    opp_patterns = count_patterns(board, Cell.OPPONENT)

    # Check for immediate wins
    if own_patterns["five"] > 0:
        return SCORE_WIN
    if opp_patterns["five"] > 0:
        return -SCORE_WIN

    # Calculate scores
    own_score = sum(SCORES[pattern] * count for pattern, count in own_patterns.items())
    opp_score = sum(SCORES[pattern] * count for pattern, count in opp_patterns.items())

    # Final evaluation: our score minus opponent's score (with defense multiplier)
    return int(own_score - opp_score * DEFENSE_MULTIPLIER)


def evaluate_move(board: Board, row: int, col: int, player: int) -> int:
    """
    Quickly evaluate the impact of a potential move.

    This is a lighter evaluation that only considers patterns
    around the specific move, rather than the entire board.
    Used for move ordering in alpha-beta search.

    Args:
        board: The game board.
        row: Row of the potential move.
        col: Column of the potential move.
        player: The player making the move.

    Returns:
        Score indicating the value of this move.
    """
    score = 0
    opponent = Cell.OPPONENT if player == Cell.OWN else Cell.OWN

    # Temporarily place the stone
    board.place_stone(row, col, player)

    # Check patterns created by this move
    for dr, dc in DIRECTIONS:
        analysis = analyze_line(board, row, col, dr, dc, player)
        pattern = classify_pattern(analysis["count"], analysis["open_ends"])
        if pattern:
            score += SCORES[pattern]

    # Remove the stone
    board.remove_stone(row, col)

    # Also consider defensive value (what opponent could do here)
    board.place_stone(row, col, opponent)

    for dr, dc in DIRECTIONS:
        analysis = analyze_line(board, row, col, dr, dc, opponent)
        pattern = classify_pattern(analysis["count"], analysis["open_ends"])
        if pattern:
            # Blocking opponent's pattern has defensive value
            score += int(SCORES[pattern] * DEFENSE_MULTIPLIER)

    board.remove_stone(row, col)

    return score


def is_winning_move(board: Board, row: int, col: int, player: int) -> bool:
    """
    Check if a move would result in a win.

    This is an optimized check used to detect immediate wins
    without full board evaluation.

    Args:
        board: The game board.
        row: Row of the potential move.
        col: Column of the potential move.
        player: The player making the move.

    Returns:
        True if this move wins the game, False otherwise.
    """
    # Temporarily place the stone
    board.place_stone(row, col, player)

    # Check if this creates five in a row
    winner = board.check_winner_at(row, col)

    # Remove the stone
    board.remove_stone(row, col)

    return winner == player


def get_threats(board: Board, player: int) -> list[tuple[int, int]]:
    """
    Find all moves that would create an immediate threat.

    A threat is a move that forces the opponent to respond or lose.
    This includes moves that create:
    - Five in a row (winning move)
    - Open four (guaranteed win next turn)

    Args:
        board: The game board.
        player: The player to find threats for.

    Returns:
        List of (row, col) positions that create threats.
    """
    threats: list[tuple[int, int]] = []

    for row in range(board.size):
        for col in range(board.size):
            if board.get_cell(row, col) != Cell.EMPTY:
                continue

            # Check if this move wins
            if is_winning_move(board, row, col, player):
                threats.append((row, col))
                continue

            # Check if this move creates an open four
            board.place_stone(row, col, player)

            for dr, dc in DIRECTIONS:
                analysis = analyze_line(board, row, col, dr, dc, player)
                if analysis["count"] == 4 and analysis["open_ends"] == 2:
                    threats.append((row, col))
                    break

            board.remove_stone(row, col)

    return threats
