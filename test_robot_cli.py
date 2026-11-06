"""Tests for the interactive tool in robot_cli.py."""

import io

from robot import Robot
from robot_cli import format_position, handle_line, run_repl


def run_session(text: str) -> list[str]:
    """Run the tool on `text` and return the printed result lines.

    The start banner and prompts are removed so tests only see results.
    """
    output = io.StringIO()
    run_repl(io.StringIO(text), output)
    lines = output.getvalue().replace("> ", "").splitlines()
    return [line for line in lines[1:] if line]


def test_format_position_shows_x_y_and_direction() -> None:
    robot = Robot()
    robot.execute("FFRFF")
    assert format_position(robot) == "x=2 y=2 facing=EAST"


def test_commands_update_and_print_position() -> None:
    assert run_session("FFRFFL\nquit\n") == ["x=2 y=2 facing=NORTH"]


def test_state_is_kept_between_lines() -> None:
    assert run_session("FF\nR\nF\nquit\n") == [
        "x=0 y=2 facing=NORTH",
        "x=0 y=2 facing=EAST",
        "x=1 y=2 facing=EAST",
    ]


def test_reset_returns_robot_to_start() -> None:
    # "reset" contains R; it must not turn the robot.
    assert run_session("FF\nreset\nquit\n") == [
        "x=0 y=2 facing=NORTH",
        "x=0 y=0 facing=NORTH",
    ]


def test_quit_stops_the_loop() -> None:
    # The F after quit must never run.
    assert run_session("quit\nF\n") == []


def test_end_of_input_stops_the_loop() -> None:
    assert run_session("F") == ["x=0 y=1 facing=NORTH"]


def test_empty_line_prints_unchanged_position() -> None:
    robot, output = handle_line(Robot(), "\n")
    assert output == "x=0 y=0 facing=NORTH"
    assert robot.position() == Robot().position()


def test_reset_and_quit_are_case_insensitive() -> None:
    assert run_session("F\n  RESET \nQuit\nF\n") == [
        "x=0 y=1 facing=NORTH",
        "x=0 y=0 facing=NORTH",
    ]
