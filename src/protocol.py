"""
Protocol module for Gomoku AI.

This module handles communication with the game manager (liskvork/Piskvork)
according to the Gomoku AI protocol specification.

=== PROTOCOL OVERVIEW ===

Communication uses standard input/output (stdin/stdout):
- Manager sends commands via stdin (one per line)
- Brain (AI) responds via stdout
- Each response must be flushed immediately

Commands are case-sensitive and follow specific formats.
The brain must handle unknown commands gracefully by responding "UNKNOWN".

=== MANDATORY COMMANDS ===

START [size]    - Initialize board of given size
TURN [X],[Y]    - Opponent made a move at (X,Y), respond with our move
BEGIN           - We play first, respond with our opening move
BOARD + DONE    - Load board state, then respond with our move
INFO [key] [val] - Receive game information (time limits, etc.)
END             - Terminate the program

=== OPTIONAL COMMANDS (implemented) ===

ABOUT           - Respond with brain metadata
RESTART         - Reset board for new game
TAKEBACK [X],[Y] - Undo a move (not fully implemented)

=== RESPONSES ===

X,Y             - A move (coordinates separated by comma)
OK              - Command successful
ERROR [msg]     - Command failed with message
UNKNOWN [msg]   - Command not recognized
MESSAGE [msg]   - Informational message for user
DEBUG [msg]     - Debug message (for development)
"""

import sys
from dataclasses import dataclass
from enum import Enum, auto

from src.board import Board, Cell

# =============================================================================
# BRAIN METADATA
# =============================================================================

BRAIN_NAME = "Azemoku"
BRAIN_VERSION = "1.0.0"
BRAIN_AUTHOR = "AI Student"
BRAIN_COUNTRY = "FR"


# =============================================================================
# COMMAND TYPES
# =============================================================================


class CommandType(Enum):
    """Enumeration of all recognized command types."""

    START = auto()
    TURN = auto()
    BEGIN = auto()
    BOARD = auto()
    INFO = auto()
    END = auto()
    ABOUT = auto()
    RESTART = auto()
    TAKEBACK = auto()
    UNKNOWN = auto()


@dataclass
class Command:
    """
    Represents a parsed command from the manager.

    Attributes:
        type: The type of command.
        args: List of arguments (strings).
        raw: The original raw command string.
    """

    type: CommandType
    args: list[str]
    raw: str


# =============================================================================
# OUTPUT FUNCTIONS
# =============================================================================


def respond(message: str) -> None:
    """
    Send a response to the manager.

    All responses must be flushed immediately to prevent deadlock.
    The manager waits for our response before proceeding.

    Args:
        message: The response message.
    """
    print(message, flush=True)


def respond_move(row: int, col: int) -> None:
    """
    Respond with a move.

    Coordinates are in X,Y format where:
    - X is the column (horizontal position)
    - Y is the row (vertical position)

    Note: The protocol uses X,Y but our internal representation
    uses (row, col) which is (Y, X). We swap here.

    Args:
        row: Row index (Y coordinate).
        col: Column index (X coordinate).
    """
    respond(f"{col},{row}")


def respond_ok() -> None:
    """Respond with OK (command successful)."""
    respond("OK")


def respond_error(message: str) -> None:
    """
    Respond with an error.

    Args:
        message: Error description.
    """
    respond(f"ERROR {message}")


def respond_unknown(command: str) -> None:
    """
    Respond to an unknown command.

    According to the protocol, the brain must not exit when
    receiving unknown commands. Instead, respond with UNKNOWN.

    Args:
        command: The unrecognized command.
    """
    respond(f"UNKNOWN command: {command}")


def send_message(message: str) -> None:
    """
    Send an informational message to the manager.

    Messages are displayed to the user but don't affect gameplay.

    Args:
        message: The message to send.
    """
    respond(f"MESSAGE {message}")


def send_debug(message: str) -> None:
    """
    Send a debug message to the manager.

    Debug messages are typically only visible during development.

    Args:
        message: The debug message.
    """
    respond(f"DEBUG {message}")


# =============================================================================
# COMMAND PARSING
# =============================================================================


def parse_command(line: str) -> Command:
    """
    Parse a command line from the manager.

    Args:
        line: Raw command string (may include trailing whitespace).

    Returns:
        Parsed Command object.
    """
    line = line.strip()

    if not line:
        return Command(CommandType.UNKNOWN, [], line)

    parts = line.split(maxsplit=1)
    cmd = parts[0].upper()
    args = parts[1].split() if len(parts) > 1 else []

    # Match command type
    match cmd:
        case "START":
            return Command(CommandType.START, args, line)
        case "TURN":
            # TURN has coordinates as single argument: "X,Y"
            return Command(CommandType.TURN, args, line)
        case "BEGIN":
            return Command(CommandType.BEGIN, args, line)
        case "BOARD":
            return Command(CommandType.BOARD, args, line)
        case "INFO":
            return Command(CommandType.INFO, args, line)
        case "END":
            return Command(CommandType.END, args, line)
        case "ABOUT":
            return Command(CommandType.ABOUT, args, line)
        case "RESTART":
            return Command(CommandType.RESTART, args, line)
        case "TAKEBACK":
            return Command(CommandType.TAKEBACK, args, line)
        case _:
            return Command(CommandType.UNKNOWN, args, line)


def parse_coordinates(coord_str: str) -> tuple[int, int] | None:
    """
    Parse coordinates from protocol format.

    The protocol uses "X,Y" format where X is column and Y is row.
    We convert to internal (row, col) format.

    Args:
        coord_str: Coordinates string in "X,Y" format.

    Returns:
        Tuple of (row, col), or None if parsing fails.
    """
    try:
        parts = coord_str.strip().split(",")
        if len(parts) != 2:
            return None
        x = int(parts[0])  # Column
        y = int(parts[1])  # Row
        return (y, x)  # Return as (row, col)
    except (ValueError, IndexError):
        return None


def parse_board_line(line: str) -> tuple[int, int, int] | None:
    """
    Parse a board state line.

    Board lines are in "X,Y,field" format where:
    - X is column
    - Y is row
    - field is 1 (own), 2 (opponent), or 3 (winning/forbidden)

    Args:
        line: Board state line.

    Returns:
        Tuple of (row, col, player), or None if parsing fails.
    """
    try:
        parts = line.strip().split(",")
        if len(parts) != 3:
            return None
        x = int(parts[0])  # Column
        y = int(parts[1])  # Row
        field = int(parts[2])  # Player (1 or 2)
        return (y, x, field)  # Return as (row, col, player)
    except (ValueError, IndexError):
        return None


# =============================================================================
# COMMAND HANDLERS
# =============================================================================


class ProtocolHandler:
    """
    Handles protocol commands and manages game state.

    This class maintains the board state and processes commands
    from the game manager, delegating to the AI for move decisions.

    Attributes:
        board: The game board.
        debug: Whether debug mode is enabled.
        timeout_turn: Time limit per turn in milliseconds.
        timeout_match: Time limit for entire match in milliseconds.
        time_left: Remaining time for the match.
        max_memory: Memory limit in bytes.
        game_type: Type of game (0=human, 1=brain, 2=tournament).
    """

    def __init__(self, debug: bool = False):
        """
        Initialize the protocol handler.

        Args:
            debug: Enable debug output.
        """
        self.board: Board | None = None
        self.debug = debug

        # Game settings (from INFO commands)
        self.timeout_turn = 5000  # 5 seconds default
        self.timeout_match = 0  # No limit
        self.time_left = 0
        self.max_memory = 70_000_000  # 70 MB default
        self.game_type = 0

    def log_debug(self, message: str) -> None:
        """Log a debug message if debug mode is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}", file=sys.stderr, flush=True)

    def handle_start(self, args: list[str]) -> bool:
        """
        Handle START command.

        Initialize a new board of the specified size.

        Args:
            args: Command arguments [size].

        Returns:
            True if successful, False otherwise.
        """
        if not args:
            respond_error("missing board size")
            return False

        try:
            size = int(args[0])
        except ValueError:
            respond_error("invalid board size")
            return False

        # Validate size
        if size < 5:
            respond_error("board too small")
            return False

        if size > 100:
            respond_error("board too large")
            return False

        # Create new board
        self.board = Board(size)
        self.log_debug(f"Initialized {size}x{size} board")
        respond_ok()
        return True

    def handle_turn(self, args: list[str]) -> bool:
        """
        Handle TURN command.

        Process opponent's move and respond with our move.

        Args:
            args: Command arguments ["X,Y"].

        Returns:
            True if successful, False otherwise.
        """
        if self.board is None:
            respond_error("game not started")
            return False

        if not args:
            respond_error("missing coordinates")
            return False

        coords = parse_coordinates(args[0])
        if coords is None:
            respond_error("invalid coordinates")
            return False

        row, col = coords

        # Place opponent's stone
        if not self.board.place_stone(row, col, Cell.OPPONENT):
            respond_error("invalid move")
            return False

        self.log_debug(f"Opponent played at ({row}, {col})")

        # Make our move
        return self._make_move()

    def handle_begin(self) -> bool:
        """
        Handle BEGIN command.

        We play first on an empty board.

        Returns:
            True if successful, False otherwise.
        """
        if self.board is None:
            respond_error("game not started")
            return False

        self.log_debug("We play first (BEGIN)")
        return self._make_move()

    def handle_board(self) -> bool:
        """
        Handle BOARD command.

        Read board state until DONE, then make our move.
        This command loads an entire board state, used for:
        - Continuing saved games
        - Undo/redo operations
        - Tournament position setup

        Returns:
            True if successful, False otherwise.
        """
        if self.board is None:
            respond_error("game not started")
            return False

        # Clear the board
        self.board.reset()

        # Read board state until DONE
        while True:
            try:
                line = input().strip()
            except EOFError:
                respond_error("unexpected end of input")
                return False

            if line.upper() == "DONE":
                break

            parsed = parse_board_line(line)
            if parsed is None:
                self.log_debug(f"Skipping invalid board line: {line}")
                continue

            row, col, field = parsed

            # Place the stone (field 1 = own, 2 = opponent, 3 = special)
            if field == 1:
                self.board.place_stone(row, col, Cell.OWN)
            elif field == 2:
                self.board.place_stone(row, col, Cell.OPPONENT)
            elif field == 3:
                # Field 3 is for winning stones or forbidden positions (renju)
                # For freestyle gomoku, treat as own stone
                self.board.place_stone(row, col, Cell.OWN)

        self.log_debug(f"Loaded board with {self.board.move_count} stones")

        # Make our move
        return self._make_move()

    def handle_info(self, args: list[str]) -> bool:
        """
        Handle INFO command.

        Store game information. No response is expected.

        Args:
            args: Command arguments [key, value].

        Returns:
            True (INFO never fails, just ignores unknown keys).
        """
        if len(args) < 2:
            return True  # Ignore malformed INFO

        key = args[0].lower()
        value = args[1]

        try:
            match key:
                case "timeout_turn":
                    self.timeout_turn = int(value)
                    self.log_debug(f"Turn timeout: {self.timeout_turn}ms")
                case "timeout_match":
                    self.timeout_match = int(value)
                    self.log_debug(f"Match timeout: {self.timeout_match}ms")
                case "time_left":
                    self.time_left = int(value)
                    self.log_debug(f"Time left: {self.time_left}ms")
                case "max_memory":
                    self.max_memory = int(value)
                    self.log_debug(f"Max memory: {self.max_memory} bytes")
                case "game_type":
                    self.game_type = int(value)
                    self.log_debug(f"Game type: {self.game_type}")
                case "rule":
                    self.log_debug(f"Rule: {value}")
                case "folder":
                    self.log_debug(f"Folder: {value}")
                case _:
                    self.log_debug(f"Unknown INFO key: {key}")
        except ValueError:
            self.log_debug(f"Invalid INFO value: {value}")

        return True

    def handle_about(self) -> bool:
        """
        Handle ABOUT command.

        Respond with brain metadata.

        Returns:
            True (always succeeds).
        """
        about = (
            f'name="{BRAIN_NAME}", '
            f'version="{BRAIN_VERSION}", '
            f'author="{BRAIN_AUTHOR}", '
            f'country="{BRAIN_COUNTRY}"'
        )
        respond(about)
        return True

    def handle_restart(self) -> bool:
        """
        Handle RESTART command.

        Reset the board for a new game (keep same size).

        Returns:
            True if successful, False otherwise.
        """
        if self.board is None:
            respond_error("game not started")
            return False

        self.board.reset()
        self.log_debug("Board reset")
        respond_ok()
        return True

    def handle_takeback(self, args: list[str]) -> bool:
        """
        Handle TAKEBACK command.

        Undo a move at the specified position.

        Args:
            args: Command arguments ["X,Y"].

        Returns:
            True if successful, False otherwise.
        """
        if self.board is None:
            respond_error("game not started")
            return False

        if not args:
            respond_error("missing coordinates")
            return False

        coords = parse_coordinates(args[0])
        if coords is None:
            respond_error("invalid coordinates")
            return False

        row, col = coords

        if not self.board.remove_stone(row, col):
            respond_error("no stone at position")
            return False

        self.log_debug(f"Removed stone at ({row}, {col})")
        respond_ok()
        return True

    def _make_move(self) -> bool:
        """
        Decide and play our move.

        This is called after processing TURN, BEGIN, or BOARD commands.

        Returns:
            True if successful, False otherwise.
        """
        # Import here to avoid circular imports
        from src.ai import find_best_move, get_opening_move

        if self.board is None:
            respond_error("no board")
            return False

        # For the very first move, use opening strategy
        if self.board.move_count == 0:
            move = get_opening_move(self.board)
            if move is None:
                respond_error("no valid moves")
                return False
            row, col = move
        else:
            move = find_best_move(self.board)
            if move is None:
                respond_error("no valid moves")
                return False
            row, col = move

        # Place our stone
        if not self.board.place_stone(row, col, Cell.OWN):
            respond_error("AI made invalid move")
            return False

        self.log_debug(f"Playing at ({row}, {col})")
        respond_move(row, col)
        return True

    def handle_command(self, line: str) -> bool:
        """
        Process a single command.

        Args:
            line: Raw command line.

        Returns:
            False if END command received, True otherwise.
        """
        command = parse_command(line)

        self.log_debug(f"Received: {command.raw}")

        match command.type:
            case CommandType.START:
                self.handle_start(command.args)
            case CommandType.TURN:
                self.handle_turn(command.args)
            case CommandType.BEGIN:
                self.handle_begin()
            case CommandType.BOARD:
                self.handle_board()
            case CommandType.INFO:
                self.handle_info(command.args)
            case CommandType.END:
                self.log_debug("Received END, terminating")
                return False
            case CommandType.ABOUT:
                self.handle_about()
            case CommandType.RESTART:
                self.handle_restart()
            case CommandType.TAKEBACK:
                self.handle_takeback(command.args)
            case CommandType.UNKNOWN:
                respond_unknown(command.raw)

        return True
