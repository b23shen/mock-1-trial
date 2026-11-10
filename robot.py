"""Simulate robots (rovers) that move on a grid from command strings.

A robot starts at (0, 0) facing North by default. North is +y and East
is +x. Commands: F = forward, B = back, L = turn left, R = turn right.

A robot moves in a "world": anything with `is_free(x, y)`. Without a
world, the grid is infinite. With a `Grid`, edges and obstacles block
moves. With a `Fleet`, other rovers block moves too. A blocked robot
stays in place; this is not an error.
"""

import warnings
from enum import Enum
from typing import Callable, Iterable, Protocol

# The default start cell: the bottom-left corner of any grid.
START: tuple[int, int] = (0, 0)


class World(Protocol):
    """Anything a robot can move in. `Grid` and `Fleet` both match this."""

    def is_free(self, x: int, y: int) -> bool:
        """Return True if a robot may enter cell (x, y)."""
        ...


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

    def __init__(
        self,
        grid: World | None = None,
        x: int = START[0],
        y: int = START[1],
        direction: Direction = Direction.NORTH,
    ) -> None:
        """Create a robot at (x, y) facing `direction`.

        Args:
            grid: The world to move in, such as a Grid or a Fleet. None
                means an infinite grid with no obstacles.
            x: Start x coordinate. Defaults to 0.
            y: Start y coordinate. Defaults to 0.
            direction: Start direction. Defaults to North.

        Raises:
            ValueError: If the start cell is not free in `grid` (off the
                grid, an obstacle, or another rover).
        """
        # The start check lives here so a single robot and a fleet share it.
        if grid is not None and not grid.is_free(x, y):
            raise ValueError(f"Start cell ({x}, {y}) is not free")
        self.grid: World | None = grid
        self.x: int = x
        self.y: int = y
        self.direction: Direction = direction
        self._actions: dict[str, Callable[[], None]] = {
            "F": self.move_forward,
            "L": self.turn_left,
            "R": self.turn_right,
            "B": self.move_backward,
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

    def move_backward(self) -> None:
        """Move one step in the current direction, if the next cell is free.

        On a grid, the robot stays in place when the next cell is off the
        grid or is an obstacle. This is not an error.
        """
        dx, dy = self.direction.delta
        next_x, next_y = self.x - dx, self.y - dy
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


class Fleet:
    """Several rovers on one grid, each with a unique integer id.

    A Fleet is also the world its rovers move in: a cell is free only if
    the grid allows it and no other rover is there. Ids start at 1 and
    are never reused, so a deleted id cannot point to a new rover.
    """

    def __init__(self, grid: Grid | None = None) -> None:
        """Create an empty fleet.

        Args:
            grid: The shared grid. None means an infinite grid.
        """
        self.grid: Grid | None = grid
        self._rovers: dict[int, Robot] = {}
        self._next_id: int = 1

    def is_free(self, x: int, y: int) -> bool:
        """Check if a rover can enter a cell.

        Args:
            x: The x coordinate.
            y: The y coordinate.

        Returns:
            True if the grid allows (x, y) and no rover is there.
        """
        if self.grid is not None and not self.grid.is_free(x, y):
            return False
        return all((r.x, r.y) != (x, y) for r in self._rovers.values())

    def add(
        self,
        x: int = START[0],
        y: int = START[1],
        direction: Direction = Direction.NORTH,
    ) -> int:
        """Place a new rover and return its id.

        Args:
            x: Start x coordinate. Defaults to 0.
            y: Start y coordinate. Defaults to 0.
            direction: Start direction. Defaults to North.

        Returns:
            The new rover's id.

        Raises:
            ValueError: If the start cell is off the grid, an obstacle,
                or holds another rover.
        """
        robot = Robot(self, x, y, direction)
        rover_id = self._next_id
        self._rovers[rover_id] = robot
        self._next_id += 1
        return rover_id

    def get(self, rover_id: int) -> Robot:
        """Return the rover with this id.

        Args:
            rover_id: The id returned by `add`.

        Returns:
            The rover.

        Raises:
            KeyError: If no rover has this id.
        """
        if rover_id not in self._rovers:
            raise KeyError(f"No rover with id {rover_id}")
        return self._rovers[rover_id]

    def delete(self, rover_id: int) -> None:
        """Remove a rover. Its cell becomes free.

        Args:
            rover_id: The id returned by `add`.

        Raises:
            KeyError: If no rover has this id.
        """
        self.get(rover_id)
        del self._rovers[rover_id]

    def execute(self, rover_id: int, commands: str) -> None:
        """Run commands on one rover. Other rovers do not move.

        Args:
            rover_id: The id returned by `add`.
            commands: The command string, for example "FFRB".

        Raises:
            KeyError: If no rover has this id.
            TypeError: If `commands` is not a string.
        """
        self.get(rover_id).execute(commands)

    def rovers(self) -> dict[int, Robot]:
        """Return all rovers by id, in the order they were added.

        Returns:
            A new dict, so callers cannot change the fleet by editing it.
        """
        return dict(self._rovers)
