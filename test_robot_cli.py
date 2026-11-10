"""Tests for the fleet command line tool in robot_cli.py."""

import io

import pytest

from robot import Fleet, Grid
from robot_cli import parse_grid, run_repl


def run_session(text: str, grid: Grid | None = None) -> list[str]:
    """Run the tool on `text` and return the printed result lines.

    The help banner and prompts are removed so tests only see results.
    """
    output = io.StringIO()
    run_repl(Fleet(grid), io.StringIO(text), output)
    lines = output.getvalue().replace("> ", "").splitlines()
    return [line for line in lines[1:] if line]


def test_parse_args_builds_grid_from_flags() -> None:
    grid = parse_grid(["--width", "5", "--height", "4", "--obstacle", "2,2"])
    assert grid is not None
    assert (grid.width, grid.height) == (5, 4)
    assert grid.obstacles == frozenset({(2, 2)})


def test_no_flags_gives_infinite_grid() -> None:
    assert parse_grid([]) is None


@pytest.mark.parametrize(
    "argv",
    [
        ["--width", "0", "--height", "5"],
        ["--width", "5", "--height", "5", "--obstacle", "0,0"],
        ["--width", "5"],
        ["--width", "5", "--height", "5", "--obstacle", "2;2"],
    ],
)
def test_invalid_grid_flags_exit_with_error(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        parse_grid(argv)
    assert exit_info.value.code == 2


def test_add_list_and_delete_rovers() -> None:
    assert run_session("add\nadd 1 0 N\nlist\ndelete 1\nlist\nquit\n") == [
        "Added rover 1: x=0 y=0 facing=NORTH",
        "Added rover 2: x=1 y=0 facing=NORTH",
        "rover 1: x=0 y=0 facing=NORTH",
        "rover 2: x=1 y=0 facing=NORTH",
        "Deleted rover 1",
        "rover 2: x=1 y=0 facing=NORTH",
    ]


def test_add_with_position_and_direction() -> None:
    assert run_session("add 3 2 w\nADD 4 4 east\n", Grid(5, 5)) == [
        "Added rover 1: x=3 y=2 facing=WEST",
        "Added rover 2: x=4 y=4 facing=EAST",
    ]


def test_rover_commands_move_only_that_rover() -> None:
    session = "add\nadd 0 2 S\n1 FF\n2 F\n2 RF\nlist\n"
    assert run_session(session, Grid(5, 5)) == [
        "Added rover 1: x=0 y=0 facing=NORTH",
        "Added rover 2: x=0 y=2 facing=SOUTH",
        "rover 1: x=0 y=1 facing=NORTH",  # second F blocked by rover 2
        "rover 2: x=0 y=2 facing=SOUTH",  # blocked by rover 1
        "rover 2: x=0 y=2 facing=WEST",  # blocked by the left edge
        "rover 1: x=0 y=1 facing=NORTH",
        "rover 2: x=0 y=2 facing=WEST",
    ]


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("7 F", "Error: No rover with id 7"),
        ("delete 7", "Error: No rover with id 7"),
        ("add 0 0 N", "Error: Start cell (0, 0) is not free"),
        ("add 1 1 X", "Error: unknown direction 'X', use N, E, S or W"),
        ("add 1", "Error: usage: add  or  add x y DIR"),
        ("jump", "Error: unknown command 'jump'."),
    ],
)
def test_errors_print_message_and_loop_continues(line: str, message: str) -> None:
    # Rover 1 sits on (0, 0); after the error, "1 F" must still work.
    lines = run_session(f"add\n{line}\n1 F\n", Grid(5, 5))
    assert lines[1].startswith(message)
    assert lines[2] == "rover 1: x=0 y=1 facing=NORTH"


def test_quit_and_end_of_input_stop_the_loop() -> None:
    # Nothing after "quit" runs.
    assert run_session("add\nQUIT\nadd 1 1 N\n") == [
        "Added rover 1: x=0 y=0 facing=NORTH",
    ]
    # No "quit": the loop ends cleanly at end of input.
    assert run_session("add") == ["Added rover 1: x=0 y=0 facing=NORTH"]
