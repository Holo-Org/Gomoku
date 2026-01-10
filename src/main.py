"""
Main module for Gomoku AI.

This is the entry point for the Gomoku brain. It:
1. Parses command-line arguments
2. Sets up the protocol handler
3. Runs the main input loop

Usage:
    ./pbrain-gomoku-ai [--debug]

Arguments:
    --debug     Enable debug output to stderr
"""

import argparse
import sys

import src.ai as ai_module
from src.protocol import ProtocolHandler


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Gomoku AI brain for liskvork/Piskvork", prog="pbrain-gomoku-ai"
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug output to stderr")

    parser.add_argument(
        "--depth", type=int, default=4, help="Search depth for minimax (default: 4)"
    )

    return parser.parse_args()


def main() -> int:
    """
    Main function.

    Sets up the protocol handler and runs the main loop,
    reading commands from stdin and processing them.

    Returns:
        Exit code (0 for success).
    """
    args = parse_args()

    # Configure AI module
    ai_module.debug_enabled = args.debug
    ai_module.DEFAULT_DEPTH = args.depth

    # Create protocol handler
    handler = ProtocolHandler(debug=args.debug)

    if args.debug:
        print(f"[DEBUG] Gomoku AI started (depth={args.depth})", file=sys.stderr, flush=True)

    # Main command loop
    try:
        while True:
            try:
                line = input()
            except EOFError:
                # End of input (pipe closed)
                if args.debug:
                    print("[DEBUG] EOF received, terminating", file=sys.stderr, flush=True)
                break

            # Process command
            if not handler.handle_command(line):
                # END command received
                break

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        if args.debug:
            print("[DEBUG] Interrupted, terminating", file=sys.stderr, flush=True)

    except Exception as e:
        # Log unexpected errors
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr, flush=True)
        if args.debug:
            import traceback

            traceback.print_exc(file=sys.stderr)
            raise  # Re-raise in debug mode for visibility
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
