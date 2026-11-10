"""Tests for the Fleet class in robot.py."""

import pytest

from robot import Direction, Fleet, Grid

N, E, S, W = Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST


def test_add_assigns_increasing_ids_starting_at_1() -> None:
    fleet = Fleet(Grid(5, 5))
    ids = [fleet.add(), fleet.add(1, 0), fleet.add(2, 0)]
    assert ids == [1, 2, 3]
    assert list(fleet.rovers()) == [1, 2, 3]


def test_add_at_given_position_and_direction() -> None:
    fleet = Fleet(Grid(5, 5))
    rover_id = fleet.add(3, 2, W)
    assert fleet.get(rover_id).position() == (3, 2, W)


@pytest.mark.parametrize(
    "cell",
    [
        (2, 2),  # obstacle
        (5, 0),  # outside the grid
        (-1, 0),  # negative coordinate
        (0, 0),  # another rover is here
    ],
)
def test_add_on_blocked_cell_raises_value_error(cell: tuple[int, int]) -> None:
    fleet = Fleet(Grid(5, 5, [(2, 2)]))
    fleet.add(0, 0)
    with pytest.raises(ValueError):
        fleet.add(*cell)
    # A failed add must not change the fleet.
    assert list(fleet.rovers()) == [1]


def test_rover_is_blocked_by_another_rover() -> None:
    fleet = Fleet(Grid(5, 5))
    a = fleet.add(0, 0, N)
    b = fleet.add(0, 2, S)
    fleet.execute(a, "FF")  # second F is blocked by b
    fleet.execute(b, "F")  # blocked by a
    assert fleet.get(a).position() == (0, 1, N)
    assert fleet.get(b).position() == (0, 2, S)


def test_rover_can_move_after_other_rover_leaves() -> None:
    fleet = Fleet(Grid(5, 5))
    a = fleet.add(0, 0, N)
    b = fleet.add(0, 1, E)
    fleet.execute(a, "F")
    assert fleet.get(a).position() == (0, 0, N)
    fleet.execute(b, "F")
    fleet.execute(a, "F")
    assert fleet.get(a).position() == (0, 1, N)
    assert fleet.get(b).position() == (1, 1, E)


def test_delete_frees_the_cell_and_id_is_not_reused() -> None:
    fleet = Fleet(Grid(5, 5))
    first = fleet.add()
    fleet.delete(first)
    second = fleet.add()  # (0, 0) is free again
    assert second == 2
    assert list(fleet.rovers()) == [2]


def test_unknown_rover_id_raises_key_error() -> None:
    fleet = Fleet(Grid(5, 5))
    fleet.add()
    with pytest.raises(KeyError, match="No rover with id 99"):
        fleet.execute(99, "F")
    with pytest.raises(KeyError, match="No rover with id 99"):
        fleet.delete(99)


def test_edges_and_obstacles_still_block_in_fleet() -> None:
    fleet = Fleet(Grid(3, 3, [(1, 1)]))
    a = fleet.add()
    b = fleet.add(1, 0, N)
    fleet.execute(a, "FFFF")  # top edge
    fleet.execute(b, "F")  # obstacle at (1, 1)
    fleet.execute(b, "B")  # bottom edge
    assert fleet.get(a).position() == (0, 2, N)
    assert fleet.get(b).position() == (1, 0, N)
