"""Tests for the Robot class in robot.py."""

from robot import Direction, Robot


def run(commands: str) -> tuple[int, int, Direction]:
    """Run commands on a new robot and return its final state."""
    robot = Robot()
    robot.execute(commands)
    return robot.position()


def test_starts_at_origin_facing_north() -> None:
    assert Robot().position() == (0, 0, Direction.NORTH)


def test_empty_command_does_nothing() -> None:
    assert run("") == (0, 0, Direction.NORTH)


def test_forward_moves_one_step_north() -> None:
    assert run("F") == (0, 1, Direction.NORTH)


def test_turn_right_four_times_returns_to_north() -> None:
    assert run("RRRR") == (0, 0, Direction.NORTH)


def test_turn_left_from_north_faces_west() -> None:
    assert run("L") == (0, 0, Direction.WEST)
    # Moving West from the origin goes into negative x.
    assert run("LF") == (-1, 0, Direction.WEST)


def test_example_ffrffl() -> None:
    assert run("FFRFFL") == (2, 2, Direction.NORTH)


def test_unknown_letters_are_ignored() -> None:
    assert run("FXF?R 9") == (0, 2, Direction.EAST)


def test_lowercase_commands_are_accepted() -> None:
    assert run("ffrffl") == run("FFRFFL")
