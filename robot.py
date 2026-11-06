"""Simulate a robot that moves on a grid from a command string.

The robot starts at (0, 0) facing North. North is +y and East is +x.
Commands: F = move forward one step, L = turn left, R = turn right.

The grid is optional. Without one, the grid is infinite. With a `Grid`,
the robot stays in place when the next cell is off the grid or blocked
by an obstacle.
"""

import warnings
from enum import Enum
from typing import Callable, Iterable

# The robot always starts here: the bottom-left corner of any grid.
START: tuple[int, int] = (0, 0)


class Direction(Enum):
    """One of the four compass directions.

    The order (N, E, S, W) is clockwise. Turning uses this order, so do
    not change it.
    """

    NORTH = (0, 1)
    EAST = (1, 0)
    SOUTH = (0, -1)
    WEST = (-1, 0)

    @property
    def delta(self) -> tuple[int, int]:
        """Return the (dx, dy) step for one move in this direction.

        Returns:
            A tuple (dx, dy) with values in {-1, 0, 1}.
        """
        return self.value


# Clockwise order, used to turn by index math instead of if/else chains.
_CLOCKWISE: list[Direction] = list(Direction)


class Grid:
    """A finite grid with optional obstacles, each filling one cell.

    Cells go from (0, 0) at the bottom-left to (width - 1, height - 1)
    at the top-right. The grid is checked once, when it is created.
    """

    def __init__(
        self,
        width: int,
        height: int,
        obstacles: Iterable[tuple[int, int]] = (),
    ) -> None:
        """Create and validate a grid.

        Args:
            width: Number of cells along x. Must be at least 1.
            height: Number of cells along y. Must be at least 1.
            obstacles: Cells the robot cannot enter, as (x, y) tuples.
                A duplicate is ignored with a UserWarning.

        Raises:
            ValueError: If width or height is below 1, or if an obstacle
                is outside the grid or on the start cell (0, 0).
        """
        if width < 1 or height < 1:
            raise ValueError(f"Grid size must be at least 1x1, got {width}x{height}")
        self.width: int = width
        self.height: int = height
        self.obstacles: frozenset[tuple[int, int]] = self._build_obstacles(obstacles)

    def _build_obstacles(
        self, obstacles: Iterable[tuple[int, int]]
    ) -> frozenset[tuple[int, int]]:
        """Validate obstacles and return them as a set without duplicates.

        Args:
            obstacles: The obstacle cells as given by the caller.

        Returns:
            The unique obstacle cells.

        Raises:
            ValueError: If an obstacle is outside the grid or on START.
        """
        unique: set[tuple[int, int]] = set()
        for cell in obstacles:
            x, y = cell
            if not self.contains(x, y):
                raise ValueError(
                    f"Obstacle {cell} is outside the {self.width}x{self.height} grid"
                )
            if cell == START:
                raise ValueError(f"Obstacle cannot be on the start cell {START}")
            if cell in unique:
                # stacklevel=3 points the warning at the code that created the Grid.
                warnings.warn(f"Duplicate obstacle at {cell} ignored", stacklevel=3)
            unique.add(cell)
        return frozenset(unique)

    def contains(self, x: int, y: int) -> bool:
        """Check if a cell is inside the grid.

        Args:
            x: The x coordinate.
            y: The y coordinate.

        Returns:
            True if (x, y) is inside the grid.
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def is_free(self, x: int, y: int) -> bool:
        """Check if the robot can enter a cell.

        Args:
            x: The x coordinate.
            y: The y coordinate.

        Returns:
            True if (x, y) is inside the grid and not an obstacle.
        """
        return self.contains(x, y) and (x, y) not in self.obstacles


class Robot:
    """A robot with a position and a facing direction.

    The state is mutable. Calling `execute` many times continues from the
    current state.
    """

    def __init__(self, grid: Grid | None = None) -> None:
        """Create a robot at (0, 0) facing North.

        Args:
            grid: The grid to move on. None means an infinite grid with
                no obstacles.
        """
        self.grid: Grid | None = grid
        self.x, self.y = START
        self.direction: Direction = Direction.NORTH
        self._actions: dict[str, Callable[[], None]] = {
            "F": self.move_forward,
            "L": self.turn_left,
            "R": self.turn_right,
        }

    def turn_left(self) -> None:
        """Turn 90 degrees counter-clockwise."""
        self._turn(-1)

    def turn_right(self) -> None:
        """Turn 90 degrees clockwise."""
        self._turn(1)

    def _turn(self, step: int) -> None:
        """Rotate by `step` quarter turns (positive = clockwise)."""
        index = _CLOCKWISE.index(self.direction)
        self.direction = _CLOCKWISE[(index + step) % len(_CLOCKWISE)]

    def move_forward(self) -> None:
        """Move one step in the current direction, if the next cell is free.

        On a grid, the robot stays in place when the next cell is off the
        grid or is an obstacle. This is not an error.
        """
        dx, dy = self.direction.delta
        next_x, next_y = self.x + dx, self.y + dy
        if self.grid is None or self.grid.is_free(next_x, next_y):
            self.x, self.y = next_x, next_y

    def execute(self, commands: str) -> None:
        """Run each command letter in order.

        Letters are case-insensitive. Unknown letters are ignored.
        An empty string does nothing.

        Args:
            commands: The command string, for example "FFRFFL".

        Raises:
            TypeError: If `commands` is not a string.
        """
        if not isinstance(commands, str):
            raise TypeError(f"commands must be a str, got {type(commands).__name__}")
        for letter in commands.upper():
            action = self._actions.get(letter)
            # Unknown letters are skipped on purpose (current requirement).
            if action is not None:
                action()

    def position(self) -> tuple[int, int, Direction]:
        """Return the current state.

        Returns:
            A tuple (x, y, direction).
        """
        return (self.x, self.y, self.direction)
