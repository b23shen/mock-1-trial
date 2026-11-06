"""Interactive command line tool to try the robot by hand.

Run it with `python robot_cli.py`, then type lines such as "FF" or "R".
The robot keeps its state between lines. Type "reset" to start again at
(0, 0) facing North, and "quit" (or press Ctrl-D) to exit.
"""

import sys
from typing import TextIO

from robot import Robot

PROMPT = "> "
HELP = "Type commands (F, L, R), 'reset' or 'quit'."


def format_position(robot: Robot) -> str:
    """Return the robot state as a short text line.

    Args:
        robot: The robot to describe.

    Returns:
        Text like "x=2 y=2 facing=NORTH".
    """
    x, y, direction = robot.position()
    return f"x={x} y={y} facing={direction.name}"


def handle_line(robot: Robot, line: str) -> tuple[Robot, str | None]:
    """Process one line of user input.

    Keywords are checked before commands, because "reset" contains the
    letter R and would otherwise turn the robot.

    Args:
        robot: The current robot.
        line: One line typed by the user.

    Returns:
        A tuple (robot, output). `robot` is a new Robot after "reset",
        otherwise the same one. `output` is the text to print, or None
        when the user typed "quit".
    """
    word = line.strip().lower()
    if word == "quit":
        return robot, None
    if word == "reset":
        robot = Robot()
    else:
        robot.execute(line.strip())
    return robot, format_position(robot)


def run_repl(input_stream: TextIO, output_stream: TextIO) -> None:
    """Read lines and run them on one robot until "quit" or end of input.

    Streams are parameters so tests can pass io.StringIO objects.

    Args:
        input_stream: Where lines are read from.
        output_stream: Where prompts and results are written.
    """
    robot = Robot()
    print(f"Start: {format_position(robot)}. {HELP}", file=output_stream)
    while True:
        print(PROMPT, end="", file=output_stream, flush=True)
        line = input_stream.readline()
        if line == "":  # End of input (Ctrl-D or end of a piped file).
            print(file=output_stream)
            return
        robot, output = handle_line(robot, line)
        if output is None:
            return
        print(output, file=output_stream)


def main() -> None:
    """Run the interactive tool on the terminal."""
    run_repl(sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
