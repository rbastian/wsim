"""Random Number Generator abstraction for game engine.

This module provides an RNG interface that supports both seeded (deterministic,
for tests and replay) and unseeded (normal play) random number generation.
"""

import random
from abc import ABC, abstractmethod


class RNG(ABC):
    """Abstract base class for random number generation."""

    @abstractmethod
    def roll_d6(self) -> int:
        """Roll a single six-sided die.

        Returns:
            An integer between 1 and 6 (inclusive).
        """
        pass

    @abstractmethod
    def roll_2d6(self) -> tuple[int, int]:
        """Roll two six-sided dice.

        Returns:
            A tuple of two integers, each between 1 and 6 (inclusive).
        """
        pass

    @abstractmethod
    def roll_dice(self, n: int, sides: int = 6) -> list[int]:
        """Roll n dice with the specified number of sides.

        Args:
            n: Number of dice to roll
            sides: Number of sides on each die (default 6)

        Returns:
            A list of n integers, each between 1 and sides (inclusive).
        """
        pass


class SeededRNG(RNG):
    """Seeded random number generator for deterministic outcomes.

    Use this for testing and replay functionality where reproducible
    results are required.
    """

    def __init__(self, seed: int):
        """Initialize with a specific seed.

        Args:
            seed: Integer seed for the random number generator
        """
        self._rng = random.Random(seed)

    def roll_d6(self) -> int:
        """Roll a single six-sided die."""
        return self._rng.randint(1, 6)

    def roll_2d6(self) -> tuple[int, int]:
        """Roll two six-sided dice."""
        return (self.roll_d6(), self.roll_d6())

    def roll_dice(self, n: int, sides: int = 6) -> list[int]:
        """Roll n dice with the specified number of sides."""
        return [self._rng.randint(1, sides) for _ in range(n)]


class UnseededRNG(RNG):
    """Unseeded random number generator for normal gameplay.

    Use this for standard gameplay where true randomness is desired.
    """

    def __init__(self):
        """Initialize with system randomness."""
        self._rng = random.Random()

    def roll_d6(self) -> int:
        """Roll a single six-sided die."""
        return self._rng.randint(1, 6)

    def roll_2d6(self) -> tuple[int, int]:
        """Roll two six-sided dice."""
        return (self.roll_d6(), self.roll_d6())

    def roll_dice(self, n: int, sides: int = 6) -> list[int]:
        """Roll n dice with the specified number of sides."""
        return [self._rng.randint(1, sides) for _ in range(n)]


def create_rng(seed: int | None = None) -> RNG:
    """Factory function to create an appropriate RNG instance.

    Args:
        seed: Optional seed for deterministic behavior. If None, creates
              an unseeded RNG for normal gameplay.

    Returns:
        RNG instance (SeededRNG if seed provided, UnseededRNG otherwise)
    """
    if seed is not None:
        return SeededRNG(seed)
    return UnseededRNG()
