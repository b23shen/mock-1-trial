"""Tests for the Robot and Grid classes in robot.py."""

import pytest

from robot import Direction, Grid, Robot

N, E, S, W = Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST


def run(commands: str, grid: Grid | None = None) -> tuple[int, int, Direction]:
    """Run commands on a new robot and return its final state."""
    robot = Robot(grid)
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


# --- Stage 2: finite grid with obstacles ---


@pytest.mark.parametrize(
    ("commands", "expected"),
    [
        ("FFFFFFF", (0, 4, N)),  # top edge
        ("RFFFFFFF", (4, 0, E)),  # right edge
        ("LF", (0, 0, W)),  # left edge
        ("LLF", (0, 0, S)),  # bottom edge
    ],
)
def test_forward_stops_at_each_edge(
    commands: str, expected: tuple[int, int, Direction]
) -> None:
    assert run(commands, Grid(5, 5)) == expected


def test_forward_stops_before_obstacle() -> None:
    assert run("FFF", Grid(5, 5, [(0, 2)])) == (0, 1, N)


def test_can_turn_and_move_after_being_blocked() -> None:
    # Blocked at (0, 1), then go around the obstacle at (0, 2).
    assert run("FFFRFLF", Grid(5, 5, [(0, 2)])) == (1, 2, N)


def test_one_by_one_grid_never_moves() -> None:
    assert run("FRFRFRF", Grid(1, 1)) == (0, 0, W)


@pytest.mark.parametrize(
    ("commands", "expected"),
    [
        ("FFF", (0, 1, N)),  # blocked by (0, 2)
        ("FRFFF", (1, 1, E)),  # blocked by (2, 1)
        ("RFFFLFFFF", (3, 2, N)),  # blocked by (3, 3)
        ("FRFLFFF", (1, 4, N)),  # passes between obstacles to the top edge
    ],
)
def test_path_around_multiple_obstacles(
    commands: str, expected: tuple[int, int, Direction]
) -> None:
    grid = Grid(5, 5, [(0, 2), (2, 1), (3, 3)])
    assert run(commands, grid) == expected


def test_robot_boxed_in_by_multiple_obstacles() -> None:
    # Obstacles above and to the right; edges below and to the left.
    assert run("FRFRFRFRF", Grid(5, 5, [(0, 1), (1, 0)])) == (0, 0, N)


@pytest.mark.parametrize(
    ("width", "height", "obstacles"),
    [
        (0, 5, []),
        (5, 0, []),
        (-1, 5, []),
        (5, 5, [(0, 0)]),  # on the start cell
        (5, 5, [(5, 0)]),  # just outside on the right
        (5, 5, [(0, 5)]),  # just outside on the top
        (5, 5, [(-1, 2)]),  # negative coordinate
    ],
)
def test_invalid_grid_raises_value_error(
    width: int, height: int, obstacles: list[tuple[int, int]]
) -> None:
    with pytest.raises(ValueError):
        Grid(width, height, obstacles)


def test_duplicate_obstacle_warns_and_is_ignored() -> None:
    with pytest.warns(UserWarning, match=r"Duplicate obstacle at \(0, 2\)"):
        grid = Grid(5, 5, [(0, 2), (2, 1), (0, 2)])
    assert grid.obstacles == frozenset({(0, 2), (2, 1)})
    assert run("FFF", grid) == (0, 1, N)
