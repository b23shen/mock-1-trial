"""Simulate a robot that moves on an infinite grid from a command string.

The robot starts at (0, 0) facing North. North is +y and East is +x.
Commands: F = move forward one step, L = turn left, R = turn right.
"""

from enum import Enum
from typing import Callable


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


class Robot:
    """A robot with a position and a facing direction.

    The state is mutable. Calling `execute` many times continues from the
    current state.
    """

    def __init__(self) -> None:
        """Create a robot at (0, 0) facing North."""
        self.x: int = 0
        self.y: int = 0
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
        """Move one step in the current direction."""
        dx, dy = self.direction.delta
        self.x += dx
        self.y += dy

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
