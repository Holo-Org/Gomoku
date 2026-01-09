"""
Board module for Gomoku game.

This module provides the Board class which represents the game state,
handles stone placement, and detects win conditions.

The board uses a 2D grid where:
- 0 (EMPTY): No stone placed
- 1 (OWN): Our stone (the AI's stone)
- 2 (OPPONENT): Opponent's stone
"""

from enum import IntEnum


class Cell(IntEnum):
    """
    Enumeration representing the possible states of a board cell.

    Values match the protocol specification:
    - EMPTY (0): No stone
    - OWN (1): Our stone (AI's stone)
    - OPPONENT (2): Opponent's stone
    """

    EMPTY = 0
    OWN = 1
    OPPONENT = 2


# Direction vectors for checking lines (horizontal, vertical, two diagonals)
# Each tuple represents (delta_row, delta_col)
DIRECTIONS = [
    (0, 1),  # Horizontal (right)
    (1, 0),  # Vertical (down)
    (1, 1),  # Diagonal (down-right)
    (1, -1),  # Anti-diagonal (down-left)
]


class Board:
    """
    Represents the Gomoku game board.

    The board is a square grid (default 20x20) where players take turns
    placing stones. The goal is to get 5 stones in a row (horizontally,
    vertically, or diagonally).

    Attributes:
        size: The dimension of the square board (e.g., 20 for 20x20).
        grid: 2D list representing the board state.
        move_count: Number of stones placed on the board.
    """

    def __init__(self, size: int = 20):
        """
        Initialize an empty board.

        Args:
            size: The dimension of the square board. Default is 20 (standard size).
        """
        self.size = size
        self.grid: list[list[int]] = [[Cell.EMPTY for _ in range(size)] for _ in range(size)]
        self.move_count = 0

    def reset(self) -> None:
        """
        Reset the board to its initial empty state.

        This is called when receiving the RESTART command.
        """
        self.grid = [[Cell.EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.move_count = 0

    def is_valid_position(self, row: int, col: int) -> bool:
        """
        Check if the given position is within the board boundaries.

        Args:
            row: Row index (0-indexed).
            col: Column index (0-indexed).

        Returns:
            True if the position is within bounds, False otherwise.
        """
        return 0 <= row < self.size and 0 <= col < self.size

    def is_valid_move(self, row: int, col: int) -> bool:
        """
        Check if a move can be made at the given position.

        A move is valid if:
        1. The position is within board boundaries.
        2. The cell is empty (no stone placed).

        Args:
            row: Row index (0-indexed).
            col: Column index (0-indexed).

        Returns:
            True if the move is valid, False otherwise.
        """
        return self.is_valid_position(row, col) and self.grid[row][col] == Cell.EMPTY

    def place_stone(self, row: int, col: int, player: int) -> bool:
        """
        Place a stone on the board.

        Args:
            row: Row index (0-indexed).
            col: Column index (0-indexed).
            player: The player placing the stone (Cell.OWN or Cell.OPPONENT).

        Returns:
            True if the stone was placed successfully, False if the move was invalid.
        """
        if not self.is_valid_move(row, col):
            return False

        self.grid[row][col] = player
        self.move_count += 1
        return True

    def remove_stone(self, row: int, col: int) -> bool:
        """
        Remove a stone from the board (used for undoing moves in search).

        Args:
            row: Row index (0-indexed).
            col: Column index (0-indexed).

        Returns:
            True if a stone was removed, False if the cell was empty.
        """
        if not self.is_valid_position(row, col) or self.grid[row][col] == Cell.EMPTY:
            return False

        self.grid[row][col] = Cell.EMPTY
        self.move_count -= 1
        return True

    def get_cell(self, row: int, col: int) -> int:
        """
        Get the state of a cell.

        Args:
            row: Row index (0-indexed).
            col: Column index (0-indexed).

        Returns:
            The cell state (EMPTY, OWN, or OPPONENT), or -1 if out of bounds.
        """
        if not self.is_valid_position(row, col):
            return -1
        return self.grid[row][col]

    def count_consecutive(self, row: int, col: int, dr: int, dc: int, player: int) -> int:
        """
        Count consecutive stones of a player in a given direction.

        Starting from (row, col), count how many consecutive stones
        of the given player exist in the direction (dr, dc).

        Args:
            row: Starting row index.
            col: Starting column index.
            dr: Row direction (-1, 0, or 1).
            dc: Column direction (-1, 0, or 1).
            player: The player whose stones to count.

        Returns:
            The number of consecutive stones (not including the starting position).
        """
        count = 0
        r, c = row + dr, col + dc

        while self.is_valid_position(r, c) and self.grid[r][c] == player:
            count += 1
            r += dr
            c += dc

        return count

    def check_winner_at(self, row: int, col: int) -> int | None:
        """
        Check if there's a winner based on the stone at the given position.

        This checks all four directions (horizontal, vertical, two diagonals)
        to see if the player at this position has 5 or more stones in a row.

        Args:
            row: Row index of the last placed stone.
            col: Column index of the last placed stone.

        Returns:
            The winning player (Cell.OWN or Cell.OPPONENT), or None if no winner.
        """
        player = self.grid[row][col]

        if player == Cell.EMPTY:
            return None

        for dr, dc in DIRECTIONS:
            # Count stones in both directions along this line
            # +1 for the stone at (row, col) itself
            count = 1
            count += self.count_consecutive(row, col, dr, dc, player)
            count += self.count_consecutive(row, col, -dr, -dc, player)

            if count >= 5:
                return player

        return None

    def check_winner(self) -> int | None:
        """
        Check if there's a winner on the entire board.

        This scans the entire board to find any winning line.
        Note: This is less efficient than check_winner_at() which only
        checks around the last move. Use this for loading board states.

        Returns:
            The winning player (Cell.OWN or Cell.OPPONENT), or None if no winner.
        """
        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] != Cell.EMPTY:
                    winner = self.check_winner_at(row, col)
                    if winner is not None:
                        return winner
        return None

    def is_full(self) -> bool:
        """
        Check if the board is completely filled.

        Returns:
            True if no empty cells remain, False otherwise.
        """
        return self.move_count >= self.size * self.size

    def get_empty_cells(self) -> list[tuple[int, int]]:
        """
        Get all empty cells on the board.

        Returns:
            List of (row, col) tuples for all empty cells.
        """
        empty: list[tuple[int, int]] = []
        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] == Cell.EMPTY:
                    empty.append((row, col))
        return empty

    def get_occupied_cells(self) -> list[tuple[int, int, int]]:
        """
        Get all occupied cells on the board.

        Returns:
            List of (row, col, player) tuples for all occupied cells.
        """
        occupied: list[tuple[int, int, int]] = []
        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] != Cell.EMPTY:
                    occupied.append((row, col, self.grid[row][col]))
        return occupied

    def copy(self) -> "Board":
        """
        Create a deep copy of the board.

        Returns:
            A new Board instance with the same state.
        """
        new_board = Board(self.size)
        new_board.grid = [row[:] for row in self.grid]
        new_board.move_count = self.move_count
        return new_board

    def __str__(self) -> str:
        """
        Create a string representation of the board for debugging.

        Uses:
        - '.' for empty cells
        - 'X' for OWN stones
        - 'O' for OPPONENT stones
        """
        symbols: dict[int, str] = {Cell.EMPTY: ".", Cell.OWN: "X", Cell.OPPONENT: "O"}
        lines: list[str] = []

        # Column headers
        header = "   " + " ".join(f"{i:2}" for i in range(self.size))
        lines.append(header)

        for row in range(self.size):
            cells = [symbols[self.grid[row][col]] for col in range(self.size)]
            row_str = f"{row:2} " + "  ".join(cells)
            lines.append(row_str)

        return "\n".join(lines)
