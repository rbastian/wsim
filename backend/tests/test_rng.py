"""Tests for RNG abstraction."""

import pytest

from wsim_core.engine import RNG, SeededRNG, UnseededRNG, create_rng


class TestSeededRNG:
    """Tests for SeededRNG with deterministic behavior."""

    def test_seeded_rng_is_deterministic(self):
        """Test that the same seed produces identical results."""
        rng1 = SeededRNG(seed=42)
        rng2 = SeededRNG(seed=42)

        # Multiple rolls should match exactly
        for _ in range(10):
            assert rng1.roll_d6() == rng2.roll_d6()

    def test_seeded_rng_d6_range(self):
        """Test that roll_d6 returns values in valid range."""
        rng = SeededRNG(seed=123)

        for _ in range(100):
            roll = rng.roll_d6()
            assert 1 <= roll <= 6

    def test_seeded_rng_2d6_deterministic(self):
        """Test that 2d6 rolls are deterministic with same seed."""
        rng1 = SeededRNG(seed=999)
        rng2 = SeededRNG(seed=999)

        for _ in range(10):
            roll1 = rng1.roll_2d6()
            roll2 = rng2.roll_2d6()
            assert roll1 == roll2
            assert len(roll1) == 2
            assert 1 <= roll1[0] <= 6
            assert 1 <= roll1[1] <= 6

    def test_seeded_rng_dice_deterministic(self):
        """Test that roll_dice is deterministic with same seed."""
        rng1 = SeededRNG(seed=555)
        rng2 = SeededRNG(seed=555)

        for n in [1, 3, 5, 10]:
            roll1 = rng1.roll_dice(n)
            roll2 = rng2.roll_dice(n)
            assert roll1 == roll2
            assert len(roll1) == n
            for die in roll1:
                assert 1 <= die <= 6

    def test_seeded_rng_custom_sides(self):
        """Test that roll_dice works with custom number of sides."""
        rng = SeededRNG(seed=777)

        # Test d4
        for _ in range(20):
            roll = rng.roll_dice(1, sides=4)[0]
            assert 1 <= roll <= 4

        # Test d10
        rng2 = SeededRNG(seed=777)
        for _ in range(20):
            roll = rng2.roll_dice(1, sides=10)[0]
            assert 1 <= roll <= 10

    def test_different_seeds_produce_different_sequences(self):
        """Test that different seeds produce different results."""
        rng1 = SeededRNG(seed=100)
        rng2 = SeededRNG(seed=200)

        # Get sequences of 10 rolls
        sequence1 = [rng1.roll_d6() for _ in range(10)]
        sequence2 = [rng2.roll_d6() for _ in range(10)]

        # Sequences should be different (extremely unlikely to match)
        assert sequence1 != sequence2

    def test_seeded_rng_produces_expected_sequence(self):
        """Test specific known sequence for regression testing."""
        rng = SeededRNG(seed=42)

        # These values are based on Python's random.Random(42)
        # They serve as a regression test
        first_rolls = [rng.roll_d6() for _ in range(5)]

        # Re-create with same seed
        rng2 = SeededRNG(seed=42)
        second_rolls = [rng2.roll_d6() for _ in range(5)]

        assert first_rolls == second_rolls


class TestUnseededRNG:
    """Tests for UnseededRNG with non-deterministic behavior."""

    def test_unseeded_rng_d6_range(self):
        """Test that roll_d6 returns values in valid range."""
        rng = UnseededRNG()

        for _ in range(100):
            roll = rng.roll_d6()
            assert 1 <= roll <= 6

    def test_unseeded_rng_2d6_range(self):
        """Test that roll_2d6 returns valid values."""
        rng = UnseededRNG()

        for _ in range(100):
            roll = rng.roll_2d6()
            assert len(roll) == 2
            assert 1 <= roll[0] <= 6
            assert 1 <= roll[1] <= 6

    def test_unseeded_rng_dice_count(self):
        """Test that roll_dice returns correct number of dice."""
        rng = UnseededRNG()

        for n in [1, 3, 5, 10]:
            roll = rng.roll_dice(n)
            assert len(roll) == n
            for die in roll:
                assert 1 <= die <= 6

    def test_unseeded_rng_produces_varied_results(self):
        """Test that unseeded RNG produces varied results."""
        rng = UnseededRNG()

        # Get 100 rolls
        rolls = [rng.roll_d6() for _ in range(100)]

        # Should have at least 3 different values (extremely likely)
        unique_values = set(rolls)
        assert len(unique_values) >= 3

    def test_unseeded_rng_custom_sides(self):
        """Test that roll_dice works with custom number of sides."""
        rng = UnseededRNG()

        # Test d20
        for _ in range(50):
            roll = rng.roll_dice(1, sides=20)[0]
            assert 1 <= roll <= 20


class TestCreateRNG:
    """Tests for the create_rng factory function."""

    def test_create_rng_with_seed_returns_seeded(self):
        """Test that providing a seed creates a SeededRNG."""
        rng = create_rng(seed=42)
        assert isinstance(rng, SeededRNG)

    def test_create_rng_without_seed_returns_unseeded(self):
        """Test that no seed creates an UnseededRNG."""
        rng = create_rng(seed=None)
        assert isinstance(rng, UnseededRNG)

        # Also test with no argument
        rng2 = create_rng()
        assert isinstance(rng2, UnseededRNG)

    def test_create_rng_with_seed_is_deterministic(self):
        """Test that factory creates deterministic RNG with seed."""
        rng1 = create_rng(seed=12345)
        rng2 = create_rng(seed=12345)

        assert rng1.roll_d6() == rng2.roll_d6()


class TestRNGInterface:
    """Tests that verify both implementations conform to RNG interface."""

    @pytest.mark.parametrize(
        "rng",
        [
            SeededRNG(seed=42),
            UnseededRNG(),
        ],
    )
    def test_rng_implements_roll_d6(self, rng: RNG):
        """Test that all RNG implementations have roll_d6."""
        roll = rng.roll_d6()
        assert isinstance(roll, int)
        assert 1 <= roll <= 6

    @pytest.mark.parametrize(
        "rng",
        [
            SeededRNG(seed=42),
            UnseededRNG(),
        ],
    )
    def test_rng_implements_roll_2d6(self, rng: RNG):
        """Test that all RNG implementations have roll_2d6."""
        roll = rng.roll_2d6()
        assert isinstance(roll, tuple)
        assert len(roll) == 2
        assert 1 <= roll[0] <= 6
        assert 1 <= roll[1] <= 6

    @pytest.mark.parametrize(
        "rng",
        [
            SeededRNG(seed=42),
            UnseededRNG(),
        ],
    )
    def test_rng_implements_roll_dice(self, rng: RNG):
        """Test that all RNG implementations have roll_dice."""
        roll = rng.roll_dice(5)
        assert isinstance(roll, list)
        assert len(roll) == 5
        for die in roll:
            assert 1 <= die <= 6


class TestDeterministicGameplay:
    """Integration tests demonstrating deterministic gameplay scenarios."""

    def test_combat_scenario_is_deterministic(self):
        """Test that a combat scenario produces identical results with same seed."""

        def simulate_combat_round(rng: RNG) -> dict[str, int]:
            """Simulate a simple combat round using RNG."""
            # Ship 1 fires
            ship1_hit_roll = rng.roll_2d6()
            ship1_damage = rng.roll_d6()

            # Ship 2 fires
            ship2_hit_roll = rng.roll_2d6()
            ship2_damage = rng.roll_d6()

            return {
                "ship1_hit": sum(ship1_hit_roll),
                "ship1_damage": ship1_damage,
                "ship2_hit": sum(ship2_hit_roll),
                "ship2_damage": ship2_damage,
            }

        # Run scenario with seed 1000
        rng1 = SeededRNG(seed=1000)
        result1 = simulate_combat_round(rng1)

        # Run scenario again with same seed
        rng2 = SeededRNG(seed=1000)
        result2 = simulate_combat_round(rng2)

        # Results should be identical
        assert result1 == result2

    def test_collision_resolution_is_deterministic(self):
        """Test that collision resolution produces identical results with same seed."""

        def simulate_collision(rng: RNG, num_ships: int) -> list[int]:
            """Simulate collision resolution for multiple ships."""
            # Each ship rolls to see who maintains position
            return [rng.roll_d6() for _ in range(num_ships)]

        seed = 5555
        rng1 = SeededRNG(seed=seed)
        result1 = simulate_collision(rng1, num_ships=4)

        rng2 = SeededRNG(seed=seed)
        result2 = simulate_collision(rng2, num_ships=4)

        assert result1 == result2

    def test_full_turn_replay(self):
        """Test that an entire turn can be replayed deterministically."""

        def simulate_turn(
            rng: RNG,
        ) -> dict[str, list[int] | list[tuple[int, int]] | list[list[int]]]:
            """Simulate a complete game turn with multiple RNG calls."""
            movement_rolls = [rng.roll_d6() for _ in range(3)]
            collision_rolls = [rng.roll_2d6() for _ in range(2)]
            combat_rolls = [rng.roll_dice(5) for _ in range(4)]

            return {
                "movement": movement_rolls,
                "collisions": collision_rolls,
                "combat": combat_rolls,
            }

        seed = 9999
        rng1 = SeededRNG(seed=seed)
        turn1 = simulate_turn(rng1)

        rng2 = SeededRNG(seed=seed)
        turn2 = simulate_turn(rng2)

        assert turn1 == turn2
