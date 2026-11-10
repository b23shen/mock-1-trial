"""Interactive command line tool to control a fleet of rovers.

Start it with an optional grid:

    python robot_cli.py --width 5 --height 5 --obstacle 2,2 --obstacle 3,1

Without --width/--height the grid is infinite. Then type lines such as:

    add              add a rover at (0, 0) facing North
    add 3 2 W        add a rover at (3, 2) facing West
    1 FFRB           run commands on rover 1
    list             show all rovers
    delete 1         remove rover 1
    quit             exit (Ctrl-D also works)

Bad input prints an error and the loop keeps running.
"""

import argparse
import sys
from typing import Sequence, TextIO

from robot import Direction, Fleet, Grid, Robot

PROMPT = "> "
HELP = "Commands: add [x y DIR], <id> <commands>, list, delete <id>, quit."

# Accept both short (N) and full (NORTH) names; input is upper-cased first.
_DIRECTIONS: dict[str, Direction] = {
    **{d.name[0]: d for d in Direction},
    **{d.name: d for d in Direction},
}


# --- Start-up flags ---


def parse_cell(text: str) -> tuple[int, int]:
    """Parse an "x,y" flag value into a cell.

    Args:
        text: Text like "2,3".

    Returns:
        The cell as (x, y).

    Raises:
        argparse.ArgumentTypeError: If the text is not two integers
            separated by a comma.
    """
    parts = text.split(",")
    try:
        x, y = (int(part) for part in parts)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected x,y but got '{text}'") from None
    return x, y


def build_parser() -> argparse.ArgumentParser:
    """Create the parser for the start-up flags.

    Returns:
        The argument parser.
    """
    parser = argparse.ArgumentParser(description="Control a fleet of rovers.")
    parser.add_argument("--width", type=int, help="grid width (needs --height)")
    parser.add_argument("--height", type=int, help="grid height (needs --width)")
    parser.add_argument(
        "--obstacle",
        type=parse_cell,
        action="append",
        default=[],
        metavar="X,Y",
        help="an obstacle cell; repeat for more",
    )
    return parser


def parse_grid(argv: Sequence[str] | None = None) -> Grid | None:
    """Build the grid from the start-up flags.

    Args:
        argv: The flags, without the program name. None reads sys.argv.

    Returns:
        A Grid, or None for an infinite grid (no size flags).

    Raises:
        SystemExit: If the flags are invalid. argparse prints the error
            and exits with code 2.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.width is None and args.height is None:
        if args.obstacle:
            parser.error("--obstacle needs --width and --height")
        return None
    if args.width is None or args.height is None:
        parser.error("--width and --height must be given together")
    try:
        return Grid(args.width, args.height, args.obstacle)
    except ValueError as error:
        parser.error(str(error))


# --- Interactive commands ---


def format_rover(rover_id: int, robot: Robot) -> str:
    """Return one rover's state as a short text line.

    Args:
        rover_id: The rover's id.
        robot: The rover.

    Returns:
        Text like "rover 1: x=2 y=2 facing=NORTH".
    """
    x, y, direction = robot.position()
    return f"rover {rover_id}: x={x} y={y} facing={direction.name}"


def _parse_int(text: str, name: str) -> int:
    """Parse an integer typed by the user.

    Raises:
        ValueError: With a clear message if `text` is not an integer.
    """
    try:
        return int(text)
    except ValueError:
        raise ValueError(f"{name} must be a whole number, got '{text}'") from None


def _parse_direction(text: str) -> Direction:
    """Parse a direction such as "N", "w" or "east".

    Raises:
        ValueError: If `text` is not a known direction.
    """
    direction = _DIRECTIONS.get(text.upper())
    if direction is None:
        raise ValueError(f"unknown direction '{text}', use N, E, S or W")
    return direction


def _handle_add(fleet: Fleet, args: list[str]) -> str:
    """Handle "add" or "add x y DIR"."""
    if not args:
        rover_id = fleet.add()
    elif len(args) == 3:
        x = _parse_int(args[0], "x")
        y = _parse_int(args[1], "y")
        rover_id = fleet.add(x, y, _parse_direction(args[2]))
    else:
        raise ValueError("usage: add  or  add x y DIR")
    return f"Added {format_rover(rover_id, fleet.get(rover_id))}"


def _handle_delete(fleet: Fleet, args: list[str]) -> str:
    """Handle "delete <id>"."""
    if len(args) != 1:
        raise ValueError("usage: delete <id>")
    rover_id = _parse_int(args[0], "id")
    fleet.delete(rover_id)
    return f"Deleted rover {rover_id}"


def _handle_list(fleet: Fleet) -> str:
    """Handle "list"."""
    rovers = fleet.rovers()
    if not rovers:
        return "No rovers."
    return "\n".join(format_rover(rid, robot) for rid, robot in rovers.items())


def _handle_move(fleet: Fleet, rover_id: int, commands: str) -> str:
    """Handle "<id> <commands>"."""
    fleet.execute(rover_id, commands)
    return format_rover(rover_id, fleet.get(rover_id))


def handle_line(fleet: Fleet, line: str) -> str | None:
    """Process one line of user input.

    Args:
        fleet: The fleet to act on.
        line: One line typed by the user.

    Returns:
        The text to print ("" for an empty line), or None when the user
        typed "quit". Errors are returned as text starting with "Error:",
        so the loop never crashes on bad input.
    """
    parts = line.split()
    if not parts:
        return ""
    word, args = parts[0].lower(), parts[1:]
    try:
        if word == "quit":
            return None
        if word == "add":
            return _handle_add(fleet, args)
        if word == "delete":
            return _handle_delete(fleet, args)
        if word == "list":
            return _handle_list(fleet)
        if word.isdigit():
            # Spaces inside commands are allowed: "1 FF R" == "1 FFR".
            return _handle_move(fleet, int(word), "".join(args))
        return f"Error: unknown command '{parts[0]}'. {HELP}"
    except (ValueError, KeyError) as error:
        # args[0] avoids the extra quotes that str(KeyError) adds.
        return f"Error: {error.args[0]}"


def run_repl(fleet: Fleet, input_stream: TextIO, output_stream: TextIO) -> None:
    """Read lines and run them on the fleet until "quit" or end of input.

    Streams are parameters so tests can pass io.StringIO objects.

    Args:
        fleet: The fleet to control.
        input_stream: Where lines are read from.
        output_stream: Where prompts and results are written.
    """
    print(HELP, file=output_stream)
    while True:
        print(PROMPT, end="", file=output_stream, flush=True)
        line = input_stream.readline()
        if line == "":  # End of input (Ctrl-D or end of a piped file).
            print(file=output_stream)
            return
        output = handle_line(fleet, line)
        if output is None:
            return
        if output:
            print(output, file=output_stream)


def main(argv: Sequence[str] | None = None) -> None:
    """Parse the flags and run the interactive tool on the terminal.

    Args:
        argv: The flags, without the program name. None reads sys.argv.
    """
    grid = parse_grid(argv)
    run_repl(Fleet(grid), sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
