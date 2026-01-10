"""
AI module for Gomoku.

This module implements the Minimax algorithm with alpha-beta pruning
for the Gomoku AI. It provides the core decision-making logic.

=== MINIMAX ALGORITHM ===

Minimax is a decision-making algorithm for two-player zero-sum games.
It assumes both players play optimally:
- The maximizing player (AI) tries to maximize the score
- The minimizing player (opponent) tries to minimize the score

The algorithm recursively explores the game tree:
1. At max nodes (AI's turn): choose the move with highest score
2. At min nodes (opponent's turn): choose the move with lowest score
3. At leaf nodes (depth limit or game over): evaluate the board

=== ALPHA-BETA PRUNING ===

Alpha-beta pruning is an optimization that eliminates branches of the
game tree that cannot affect the final decision:
- Alpha: best score the maximizer can guarantee (lower bound)
- Beta: best score the minimizer can guarantee (upper bound)

When alpha >= beta, we can prune (stop searching) because:
- The maximizer won't choose this path (has a better option)
- The minimizer won't allow this path (has a better option)

This can dramatically reduce the number of nodes evaluated.

=== MOVE ORDERING ===

The effectiveness of alpha-beta pruning depends heavily on the order
in which moves are evaluated. Better move ordering leads to more pruning.

Two implementations are provided:
1. Simple: Consider moves near existing stones (no ordering)
2. With ordering: Sort moves by preliminary evaluation score
"""

import sys

from src.board import Board, Cell
from src.evaluation import (
    SCORE_WIN,
    evaluate_board,
    is_winning_move,
)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Default search depth for Minimax
DEFAULT_DEPTH = 4

# Maximum distance from existing stones to consider for candidate moves
# This significantly reduces the search space
CANDIDATE_RADIUS = 2

# Enable debug output (controlled by main.py)
debug_enabled = False


def debug(message: str) -> None:
    """Print debug message to stderr if debugging is enabled."""
    if debug_enabled:
        print(f"DEBUG {message}", file=sys.stderr, flush=True)


# =============================================================================
# CANDIDATE MOVE GENERATION
# =============================================================================


def get_candidate_moves_simple(board: Board) -> list[tuple[int, int]]:
    """
    Get candidate moves without ordering (simple version).

    This function returns all empty cells within CANDIDATE_RADIUS
    of any existing stone. This dramatically reduces the search space
    compared to considering all empty cells.

    For an empty board, returns the center position.

    Args:
        board: The game board.

    Returns:
        List of (row, col) candidate positions.

    Why limit to nearby cells?
    ==========================
    In Gomoku, good moves are almost always near existing stones.
    Playing far from all stones is rarely beneficial. By limiting
    candidates to nearby cells, we can search deeper with the same
    computational budget.
    """
    if board.move_count == 0:
        # Empty board: play in the center
        center = board.size // 2
        return [(center, center)]

    candidates: set[tuple[int, int]] = set()

    # Find all cells near existing stones
    for row, col, _ in board.get_occupied_cells():
        # Add all empty cells within radius
        for dr in range(-CANDIDATE_RADIUS, CANDIDATE_RADIUS + 1):
            for dc in range(-CANDIDATE_RADIUS, CANDIDATE_RADIUS + 1):
                nr, nc = row + dr, col + dc
                if board.is_valid_move(nr, nc):
                    candidates.add((nr, nc))

    return list(candidates)


# =============================================================================
# MOVE ORDERING IMPLEMENTATIONS
# =============================================================================
# Uncomment ONE of the following two functions to choose the implementation.
# The "with ordering" version is generally stronger but slightly slower per node.

# -----------------------------------------------------------------------------
# VERSION 1: Simple (no ordering) - Currently ACTIVE
# -----------------------------------------------------------------------------


def get_candidate_moves(board: Board, _player: int) -> list[tuple[int, int]]:
    """
    Get candidate moves without ordering.

    This is the simple version that just returns nearby empty cells
    without any sorting. It's faster per call but may result in
    less alpha-beta pruning.

    Args:
        board: The game board.
        player: The player to move (used for consistency with ordered version).

    Returns:
        List of (row, col) candidate positions.
    """
    return get_candidate_moves_simple(board)


# -----------------------------------------------------------------------------
# VERSION 2: With move ordering - Currently INACTIVE (uncomment to enable)
# -----------------------------------------------------------------------------

# def get_candidate_moves(board: Board, player: int) -> list[tuple[int, int]]:
#     """
#     Get candidate moves with move ordering.
#
#     This version evaluates each candidate move and sorts them by
#     their preliminary score. Better moves are evaluated first,
#     which leads to more alpha-beta pruning.
#
#     The tradeoff is that we spend more time generating moves,
#     but save time by pruning more branches.
#
#     Args:
#         board: The game board.
#         player: The player to move.
#
#     Returns:
#         List of (row, col) candidate positions, sorted by estimated value.
#     """
#     candidates = get_candidate_moves_simple(board)
#
#     if not candidates:
#         return candidates
#
#     # First, check for immediate wins (always consider these first)
#     winning_moves = []
#     other_moves = []
#
#     for row, col in candidates:
#         if is_winning_move(board, row, col, player):
#             winning_moves.append((row, col))
#         else:
#             other_moves.append((row, col))
#
#     # If there are winning moves, prioritize them
#     if winning_moves:
#         return winning_moves + other_moves
#
#     # Check for opponent's winning moves (must block)
#     opponent = Cell.OPPONENT if player == Cell.OWN else Cell.OWN
#     blocking_moves = []
#     remaining_moves = []
#
#     for row, col in other_moves:
#         if is_winning_move(board, row, col, opponent):
#             blocking_moves.append((row, col))
#         else:
#             remaining_moves.append((row, col))
#
#     # If opponent has winning moves, prioritize blocking
#     if blocking_moves:
#         return blocking_moves + remaining_moves
#
#     # Sort remaining moves by their evaluated potential
#     scored_moves = [
#         (evaluate_move(board, row, col, player), row, col)
#         for row, col in remaining_moves
#     ]
#     scored_moves.sort(reverse=True)  # Highest scores first
#
#     return [(row, col) for _, row, col in scored_moves]


# =============================================================================
# MINIMAX WITH ALPHA-BETA PRUNING
# =============================================================================


def minimax(
    board: Board,
    depth: int,
    alpha: int,
    beta: int,
    maximizing: bool,
    last_move: tuple[int, int] | None = None,
) -> int:
    """
    Minimax algorithm with alpha-beta pruning.

    This function recursively evaluates the game tree to find the
    best possible outcome assuming optimal play from both sides.

    Args:
        board: The current game board.
        depth: Remaining search depth.
        alpha: Best score the maximizer can guarantee so far.
        beta: Best score the minimizer can guarantee so far.
        maximizing: True if it's the maximizing player's (AI's) turn.
        last_move: The last move made (for win checking optimization).

    Returns:
        The evaluation score of the best path from this position.

    Algorithm:
    ==========

    1. Check terminal conditions:
       - If last move won the game, return ±SCORE_WIN
       - If depth is 0, return static evaluation

    2. Generate candidate moves

    3. For each candidate move:
       a. Make the move
       b. Recursively call minimax for opponent
       c. Undo the move
       d. Update alpha/beta
       e. Prune if alpha >= beta

    4. Return the best score found
    """
    # Check if the game is over (someone won with last move)
    if last_move is not None:
        winner = board.check_winner_at(last_move[0], last_move[1])
        if winner == Cell.OWN:
            return SCORE_WIN + depth  # Prefer faster wins
        if winner == Cell.OPPONENT:
            return -SCORE_WIN - depth  # Prefer slower losses

    # Check if we've reached the depth limit
    if depth == 0:
        return evaluate_board(board)

    # Determine current player
    player = Cell.OWN if maximizing else Cell.OPPONENT

    # Get candidate moves
    candidates = get_candidate_moves(board, player)

    # If no candidates (board is full), return evaluation
    if not candidates:
        return evaluate_board(board)

    if maximizing:
        # Maximizing player (AI) - find the highest score
        max_eval = -SCORE_WIN * 10  # Use a very negative value instead of -inf

        for row, col in candidates:
            # Make the move
            board.place_stone(row, col, Cell.OWN)

            # Recursive evaluation
            eval_score = minimax(board, depth - 1, alpha, beta, False, (row, col))

            # Undo the move
            board.remove_stone(row, col)

            # Update best score
            max_eval = max(max_eval, eval_score)

            # Update alpha
            alpha = max(alpha, eval_score)

            # Alpha-beta pruning
            if beta <= alpha:
                debug(f"Pruned at depth {depth}, alpha={alpha}, beta={beta}")
                break

        return max_eval

    # Minimizing player (opponent) - find the lowest score
    min_eval = SCORE_WIN * 10  # Use a very positive value instead of +inf

    for row, col in candidates:
        # Make the move
        board.place_stone(row, col, Cell.OPPONENT)

        # Recursive evaluation
        eval_score = minimax(board, depth - 1, alpha, beta, True, (row, col))

        # Undo the move
        board.remove_stone(row, col)

        # Update best score
        min_eval = min(min_eval, eval_score)

        # Update beta
        beta = min(beta, eval_score)

        # Alpha-beta pruning
        if beta <= alpha:
            debug(f"Pruned at depth {depth}, alpha={alpha}, beta={beta}")
            break

    return min_eval


# =============================================================================
# MAIN AI INTERFACE
# =============================================================================


def find_best_move(board: Board, depth: int = DEFAULT_DEPTH) -> tuple[int, int] | None:
    """
    Find the best move for the AI.

    This is the main entry point for the AI. It uses minimax with
    alpha-beta pruning to search for the optimal move.

    Args:
        board: The current game board.
        depth: Search depth (default: DEFAULT_DEPTH).

    Returns:
        The best move as (row, col), or None if no valid moves.

    Optimization Notes:
    ===================

    1. Before deep search, check for immediate wins
    2. Check if opponent has winning move (must block)
    3. Use alpha-beta pruning to reduce search space
    """
    debug(f"Finding best move at depth {depth}")

    # Get candidate moves
    candidates = get_candidate_moves(board, Cell.OWN)

    if not candidates:
        return None

    # Quick check: can we win immediately?
    for row, col in candidates:
        if is_winning_move(board, row, col, Cell.OWN):
            debug(f"Found immediate win at ({row}, {col})")
            return (row, col)

    # Quick check: must we block opponent's win?
    for row, col in candidates:
        if is_winning_move(board, row, col, Cell.OPPONENT):
            debug(f"Blocking opponent's win at ({row}, {col})")
            return (row, col)

    # Full minimax search
    best_move = None
    best_score = -SCORE_WIN * 10
    alpha = -SCORE_WIN * 10
    beta = SCORE_WIN * 10

    for row, col in candidates:
        # Make the move
        board.place_stone(row, col, Cell.OWN)

        # Evaluate with minimax (opponent's turn, so minimizing)
        score = minimax(board, depth - 1, alpha, beta, False, (row, col))

        # Undo the move
        board.remove_stone(row, col)

        debug(f"Move ({row}, {col}) scored {score}")

        # Update best move
        if score > best_score:
            best_score = score
            best_move = (row, col)
            alpha = max(alpha, score)

    debug(f"Best move: {best_move} with score {best_score}")
    return best_move


def get_opening_move(board: Board) -> tuple[int, int] | None:
    """
    Get a move for the opening (first few moves).

    For the very first move, playing in the center is standard.
    This function can be extended for more sophisticated openings.

    Args:
        board: The current game board.

    Returns:
        A position for the opening move, or None if the board is full.
    """
    center = board.size // 2

    # If center is available, play there
    if board.is_valid_move(center, center):
        return (center, center)

    # Otherwise, play near center
    for dr in range(-1, 2):
        for dc in range(-1, 2):
            if board.is_valid_move(center + dr, center + dc):
                return (center + dr, center + dc)

    # Fallback to regular search
    move = find_best_move(board)
    if move is not None:
        return move
    # This should never happen in a real opening, but handle gracefully
    empty_cells = board.get_empty_cells()
    return empty_cells[0] if empty_cells else None
