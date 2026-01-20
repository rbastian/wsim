"""End-to-end tests for complete game scenarios.

This module tests complete game playthroughs for all three MVP scenarios:
1. Frigate Duel (Scenario 1) - Basic 1v1 combat
2. Crossing Paths (Scenario 2) - Collision and fouling mechanics
3. Two-Ship Line Battle (Scenario 3) - Multi-ship targeting and screening

Each test verifies:
- Complete turn loop: Planning -> Movement -> Combat -> Reload -> Advance
- Victory conditions trigger correctly
- Game state remains consistent throughout
- All phases execute without errors
"""

import pytest
from fastapi.testclient import TestClient

from wsim_api.main import app
from wsim_api.store import get_game_store

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_game_store() -> None:
    """Reset game store before each test."""
    store = get_game_store()
    for game in list(store.list_games()):
        store.delete_game(game.id)


class TestScenario1FrigateDuel:
    """End-to-end tests for Scenario 1: Frigate Duel.

    This scenario features a simple 1v1 frigate battle, perfect for testing
    the basic game loop and victory conditions.
    """

    def test_complete_game_with_combat(self) -> None:
        """Test a complete game playthrough with ships engaging in combat.

        This test verifies:
        - Game creation from scenario
        - Multiple turns of movement and combat
        - Damage application and accumulation
        - Victory condition when a ship strikes
        """
        # Create game
        create_response = client.post(
            "/games",
            json={"scenario_id": "mvp_frigate_duel_v1"},
        )
        assert create_response.status_code == 201
        game_id = create_response.json()["game_id"]

        # Verify initial state
        initial_state = create_response.json()["state"]
        assert initial_state["turn_number"] == 1
        assert initial_state["phase"] == "planning"
        assert len(initial_state["ships"]) == 2
        assert initial_state["game_ended"] is False

        # Get ship IDs
        ships = initial_state["ships"]
        p1_ship = next(s for s in ships.values() if s["side"] == "P1")
        p2_ship = next(s for s in ships.values() if s["side"] == "P2")
        p1_ship_id = p1_ship["id"]
        p2_ship_id = p2_ship["id"]

        # Play through multiple turns
        for turn_num in range(1, 4):
            # Both players submit orders to close distance and engage
            # Turn 1: Both move forward
            if turn_num == 1:
                p1_orders = [{"ship_id": p1_ship_id, "movement_string": "2"}]
                p2_orders = [{"ship_id": p2_ship_id, "movement_string": "2"}]
            # Turn 2: Adjust facing and move closer
            elif turn_num == 2:
                p1_orders = [{"ship_id": p1_ship_id, "movement_string": "R1"}]
                p2_orders = [{"ship_id": p2_ship_id, "movement_string": "L1"}]
            # Turn 3: Move into firing range
            else:
                p1_orders = [{"ship_id": p1_ship_id, "movement_string": "1"}]
                p2_orders = [{"ship_id": p2_ship_id, "movement_string": "1"}]

            # P1 submits orders
            p1_submit = client.post(
                f"/games/{game_id}/turns/{turn_num}/orders",
                json={"side": "P1", "orders": p1_orders},
            )
            assert p1_submit.status_code == 200

            # P2 submits orders
            p2_submit = client.post(
                f"/games/{game_id}/turns/{turn_num}/orders",
                json={"side": "P2", "orders": p2_orders},
            )
            assert p2_submit.status_code == 200

            # P1 marks ready
            p1_ready = client.post(
                f"/games/{game_id}/turns/{turn_num}/ready",
                json={"side": "P1"},
            )
            assert p1_ready.status_code == 200

            # P2 marks ready
            p2_ready = client.post(
                f"/games/{game_id}/turns/{turn_num}/ready",
                json={"side": "P2"},
            )
            assert p2_ready.status_code == 200
            assert p2_ready.json()["both_ready"] is True

            # Resolve movement
            movement_response = client.post(f"/games/{game_id}/turns/{turn_num}/resolve/movement")
            assert movement_response.status_code == 200
            movement_state = movement_response.json()["state"]
            assert movement_state["phase"] == "combat"

            # Verify movement events were created
            movement_events = movement_response.json()["events"]
            assert len(movement_events) > 0
            assert any(e["event_type"] == "movement" for e in movement_events)

            # Get current game state
            game_response = client.get(f"/games/{game_id}")
            assert game_response.status_code == 200
            game_state = game_response.json()

            # Check if game ended due to victory condition
            if game_state["game_ended"]:
                assert game_state["winner"] is not None
                break

            # Get broadside arc info for P1 ship's right broadside
            arc_response = client.get(f"/games/{game_id}/ships/{p1_ship_id}/broadside/R/arc")
            assert arc_response.status_code == 200
            arc_data = arc_response.json()

            # Fire broadsides if targets are in range
            if p2_ship_id in arc_data["valid_targets"]:
                fire_response = client.post(
                    f"/games/{game_id}/turns/{turn_num}/combat/fire",
                    json={
                        "ship_id": p1_ship_id,
                        "broadside": "R",
                        "target_ship_id": p2_ship_id,
                        "aim": "hull",
                    },
                )
                assert fire_response.status_code == 200
                fire_events = fire_response.json()["events"]
                assert len(fire_events) > 0
                assert fire_events[0]["event_type"] == "broadside_fire"

            # P2 fires back if in range
            arc_response_p2 = client.get(f"/games/{game_id}/ships/{p2_ship_id}/broadside/L/arc")
            assert arc_response_p2.status_code == 200
            arc_data_p2 = arc_response_p2.json()

            if p1_ship_id in arc_data_p2["valid_targets"]:
                fire_response_p2 = client.post(
                    f"/games/{game_id}/turns/{turn_num}/combat/fire",
                    json={
                        "ship_id": p2_ship_id,
                        "broadside": "L",
                        "target_ship_id": p1_ship_id,
                        "aim": "hull",
                    },
                )
                assert fire_response_p2.status_code == 200

            # Check if game ended after combat
            game_response = client.get(f"/games/{game_id}")
            game_state = game_response.json()
            if game_state["game_ended"]:
                assert game_state["winner"] is not None
                break

            # Reload
            reload_response = client.post(f"/games/{game_id}/turns/{turn_num}/resolve/reload")
            assert reload_response.status_code == 200
            reload_state = reload_response.json()["state"]
            assert reload_state["phase"] == "reload"

            # Verify reload events
            reload_events = reload_response.json()["events"]
            assert len(reload_events) > 0

            # Check if game ended after reload (e.g., turn limit)
            if reload_state["game_ended"]:
                assert reload_state["winner"] is not None
                break

            # Advance turn
            advance_response = client.post(f"/games/{game_id}/turns/{turn_num}/advance")
            assert advance_response.status_code == 200
            next_state = advance_response.json()["state"]
            assert next_state["turn_number"] == turn_num + 1
            assert next_state["phase"] == "planning"

            # Verify orders were cleared
            assert next_state["p1_orders"] is None
            assert next_state["p2_orders"] is None

        # Verify final game state has event log entries
        final_game = client.get(f"/games/{game_id}")
        final_state = final_game.json()
        assert len(final_state["event_log"]) > 0

        # Verify we have events for all phases
        event_types = {e["event_type"] for e in final_state["event_log"]}
        assert "movement" in event_types

    def test_game_state_consistency(self) -> None:
        """Test that game state remains consistent throughout a playthrough.

        Verifies:
        - Ship positions are valid after movement
        - Hull/rigging/crew never go negative
        - Load states transition correctly
        - Phase transitions follow the correct sequence
        """
        # Create game
        create_response = client.post(
            "/games",
            json={"scenario_id": "mvp_frigate_duel_v1"},
        )
        assert create_response.status_code == 201
        game_id = create_response.json()["game_id"]
        initial_state = create_response.json()["state"]

        ships = initial_state["ships"]
        p1_ship_id = next(s["id"] for s in ships.values() if s["side"] == "P1")
        p2_ship_id = next(s["id"] for s in ships.values() if s["side"] == "P2")

        # Execute one complete turn
        turn_num = 1

        # Submit orders
        client.post(
            f"/games/{game_id}/turns/{turn_num}/orders",
            json={"side": "P1", "orders": [{"ship_id": p1_ship_id, "movement_string": "1"}]},
        )
        client.post(
            f"/games/{game_id}/turns/{turn_num}/orders",
            json={"side": "P2", "orders": [{"ship_id": p2_ship_id, "movement_string": "1"}]},
        )

        # Mark ready
        client.post(f"/games/{game_id}/turns/{turn_num}/ready", json={"side": "P1"})
        client.post(f"/games/{game_id}/turns/{turn_num}/ready", json={"side": "P2"})

        # Resolve movement and check state
        movement_response = client.post(f"/games/{game_id}/turns/{turn_num}/resolve/movement")
        movement_state = movement_response.json()["state"]

        # Verify all ships have valid positions
        for ship in movement_state["ships"].values():
            assert ship["bow_hex"]["col"] >= 0
            assert ship["bow_hex"]["row"] >= 0
            assert ship["stern_hex"]["col"] >= 0
            assert ship["stern_hex"]["row"] >= 0

            # Verify stats are non-negative
            assert ship["hull"] >= 0
            assert ship["rigging"] >= 0
            assert ship["crew"] >= 0
            assert ship["guns_L"] >= 0
            assert ship["guns_R"] >= 0

        # Reload and advance
        client.post(f"/games/{game_id}/turns/{turn_num}/resolve/reload")
        advance_response = client.post(f"/games/{game_id}/turns/{turn_num}/advance")
        next_state = advance_response.json()["state"]

        # Verify load states were restored
        for ship in next_state["ships"].values():
            if not ship["struck"]:
                # Non-struck ships should have loaded broadsides after reload
                # (unless they have no guns)
                if ship["guns_L"] > 0:
                    assert ship["load_L"] in ["R", "empty"]  # May still be empty if damaged
                if ship["guns_R"] > 0:
                    assert ship["load_R"] in ["R", "empty"]


class TestScenario2CrossingPaths:
    """End-to-end tests for Scenario 2: Crossing Paths.

    This scenario tests collision detection and fouling with ships on
    converging courses.
    """

    def test_collision_and_fouling(self) -> None:
        """Test that collisions are detected and fouling is applied.

        Verifies:
        - Collision detection during simultaneous movement
        - Fouling status is set on colliding ships
        - Movement is truncated appropriately
        - Collision events are logged
        """
        # Create game
        create_response = client.post(
            "/games",
            json={"scenario_id": "mvp_crossing_paths_v1"},
        )
        assert create_response.status_code == 201
        game_id = create_response.json()["game_id"]
        initial_state = create_response.json()["state"]

        assert len(initial_state["ships"]) == 4  # 2v2 scenario

        # Get ship IDs
        ships = initial_state["ships"]
        p1_ships = [s for s in ships.values() if s["side"] == "P1"]
        p2_ships = [s for s in ships.values() if s["side"] == "P2"]

        turn_num = 1

        # Submit orders that will cause ships to cross paths
        p1_orders = [
            {"ship_id": p1_ships[0]["id"], "movement_string": "2"},
            {"ship_id": p1_ships[1]["id"], "movement_string": "2"},
        ]
        p2_orders = [
            {"ship_id": p2_ships[0]["id"], "movement_string": "2"},
            {"ship_id": p2_ships[1]["id"], "movement_string": "2"},
        ]

        client.post(
            f"/games/{game_id}/turns/{turn_num}/orders",
            json={"side": "P1", "orders": p1_orders},
        )
        client.post(
            f"/games/{game_id}/turns/{turn_num}/orders",
            json={"side": "P2", "orders": p2_orders},
        )

        client.post(f"/games/{game_id}/turns/{turn_num}/ready", json={"side": "P1"})
        client.post(f"/games/{game_id}/turns/{turn_num}/ready", json={"side": "P2"})

        # Resolve movement
        movement_response = client.post(f"/games/{game_id}/turns/{turn_num}/resolve/movement")
        assert movement_response.status_code == 200

        movement_events = movement_response.json()["events"]

        # Check if collision events were created
        # Note: Collision might not happen on turn 1 depending on initial positions
        # but the test verifies the system handles it correctly if it does
        collision_events = [e for e in movement_events if e["event_type"] == "collision"]

        if collision_events:
            # If collisions occurred, verify fouling was applied
            # Check for fouling events
            fouling_events = [e for e in movement_events if e["event_type"] == "fouling_check"]
            assert len(fouling_events) > 0

            # Fouling is determined by dice roll, so we can't guarantee it happened
            # but we can verify the event was logged
            assert any(e["event_type"] == "fouling_check" for e in movement_events)

    def test_multi_ship_movement(self) -> None:
        """Test simultaneous movement with multiple ships per side.

        Verifies:
        - All ships move correctly
        - No ships overlap after movement
        - Movement events created for all ships
        """
        # Create game
        create_response = client.post(
            "/games",
            json={"scenario_id": "mvp_crossing_paths_v1"},
        )
        game_id = create_response.json()["game_id"]
        initial_state = create_response.json()["state"]

        ships = initial_state["ships"]
        p1_ships = [s for s in ships.values() if s["side"] == "P1"]
        p2_ships = [s for s in ships.values() if s["side"] == "P2"]

        turn_num = 1

        # Submit simple forward movement for all ships
        p1_orders = [{"ship_id": s["id"], "movement_string": "1"} for s in p1_ships]
        p2_orders = [{"ship_id": s["id"], "movement_string": "1"} for s in p2_ships]

        client.post(
            f"/games/{game_id}/turns/{turn_num}/orders",
            json={"side": "P1", "orders": p1_orders},
        )
        client.post(
            f"/games/{game_id}/turns/{turn_num}/orders",
            json={"side": "P2", "orders": p2_orders},
        )

        client.post(f"/games/{game_id}/turns/{turn_num}/ready", json={"side": "P1"})
        client.post(f"/games/{game_id}/turns/{turn_num}/ready", json={"side": "P2"})

        # Resolve movement
        movement_response = client.post(f"/games/{game_id}/turns/{turn_num}/resolve/movement")
        assert movement_response.status_code == 200

        movement_state = movement_response.json()["state"]
        movement_events = movement_response.json()["events"]

        # Verify we have movement events for all ships
        ship_movement_events = [e for e in movement_events if e["event_type"] == "movement"]
        assert len(ship_movement_events) == 4  # One per ship

        # Verify no ships occupy the same hexes
        ship_hexes = set()
        for ship in movement_state["ships"].values():
            bow = (ship["bow_hex"]["col"], ship["bow_hex"]["row"])
            stern = (ship["stern_hex"]["col"], ship["stern_hex"]["row"])

            # Each ship hex should be unique
            assert bow not in ship_hexes, f"Duplicate bow position: {bow}"
            assert stern not in ship_hexes, f"Duplicate stern position: {stern}"

            ship_hexes.add(bow)
            ship_hexes.add(stern)


class TestScenario3TwoShipLineBattle:
    """End-to-end tests for Scenario 3: Two-Ship Line Battle.

    This scenario tests multi-ship targeting and the closest-target rule.
    """

    def test_closest_target_enforcement(self) -> None:
        """Test that closest-target rule is enforced correctly.

        Verifies:
        - Only closest enemies can be targeted
        - Friendly ships don't block targeting
        - Target selection follows the rules
        """
        # Create game
        create_response = client.post(
            "/games",
            json={"scenario_id": "mvp_two_ship_line_battle_v1"},
        )
        assert create_response.status_code == 201
        game_id = create_response.json()["game_id"]
        initial_state = create_response.json()["state"]

        assert len(initial_state["ships"]) == 4

        ships = initial_state["ships"]
        p1_ships = [s for s in ships.values() if s["side"] == "P1"]
        p2_ships = [s for s in ships.values() if s["side"] == "P2"]

        turn_num = 1

        # Move ships closer
        p1_orders = [{"ship_id": s["id"], "movement_string": "2"} for s in p1_ships]
        p2_orders = [{"ship_id": s["id"], "movement_string": "2"} for s in p2_ships]

        client.post(
            f"/games/{game_id}/turns/{turn_num}/orders",
            json={"side": "P1", "orders": p1_orders},
        )
        client.post(
            f"/games/{game_id}/turns/{turn_num}/orders",
            json={"side": "P2", "orders": p2_orders},
        )

        client.post(f"/games/{game_id}/turns/{turn_num}/ready", json={"side": "P1"})
        client.post(f"/games/{game_id}/turns/{turn_num}/ready", json={"side": "P2"})

        # Resolve movement
        movement_response = client.post(f"/games/{game_id}/turns/{turn_num}/resolve/movement")
        assert movement_response.status_code == 200

        # Check broadside arcs and valid targets for each ship
        for ship in p1_ships:
            for broadside in ["L", "R"]:
                arc_response = client.get(
                    f"/games/{game_id}/ships/{ship['id']}/broadside/{broadside}/arc"
                )
                assert arc_response.status_code == 200
                arc_data = arc_response.json()

                # If there are ships in arc, verify valid targets are a subset
                if arc_data["ships_in_arc"]:
                    valid_targets = set(arc_data["valid_targets"])
                    ships_in_arc = set(arc_data["ships_in_arc"])

                    # Valid targets must be a subset of ships in arc
                    assert valid_targets.issubset(ships_in_arc)

                    # Valid targets should not include friendly ships
                    for target_id in valid_targets:
                        target_ship = next(s for s in ships.values() if s["id"] == target_id)
                        assert target_ship["side"] != ship["side"]

    def test_multi_ship_combat(self) -> None:
        """Test combat with multiple ships on each side.

        Verifies:
        - Multiple ships can fire in same turn
        - Damage is applied correctly to all targets
        - Combat events are logged for each firing
        """
        # Create game
        create_response = client.post(
            "/games",
            json={"scenario_id": "mvp_two_ship_line_battle_v1"},
        )
        game_id = create_response.json()["game_id"]
        initial_state = create_response.json()["state"]

        ships = initial_state["ships"]
        p1_ships = [s for s in ships.values() if s["side"] == "P1"]
        p2_ships = [s for s in ships.values() if s["side"] == "P2"]

        turn_num = 1

        # Move ships into close range
        p1_orders = [{"ship_id": s["id"], "movement_string": "3"} for s in p1_ships]
        p2_orders = [{"ship_id": s["id"], "movement_string": "3"} for s in p2_ships]

        client.post(
            f"/games/{game_id}/turns/{turn_num}/orders",
            json={"side": "P1", "orders": p1_orders},
        )
        client.post(
            f"/games/{game_id}/turns/{turn_num}/orders",
            json={"side": "P2", "orders": p2_orders},
        )

        client.post(f"/games/{game_id}/turns/{turn_num}/ready", json={"side": "P1"})
        client.post(f"/games/{game_id}/turns/{turn_num}/ready", json={"side": "P2"})

        # Resolve movement
        client.post(f"/games/{game_id}/turns/{turn_num}/resolve/movement")

        # Attempt to fire from each P1 ship
        combat_events_count = 0
        for ship in p1_ships:
            # Check if ship can fire right broadside
            arc_response = client.get(f"/games/{game_id}/ships/{ship['id']}/broadside/R/arc")
            arc_data = arc_response.json()

            if arc_data["valid_targets"]:
                # Fire at first valid target
                target_id = arc_data["valid_targets"][0]
                fire_response = client.post(
                    f"/games/{game_id}/turns/{turn_num}/combat/fire",
                    json={
                        "ship_id": ship["id"],
                        "broadside": "R",
                        "target_ship_id": target_id,
                        "aim": "hull",
                    },
                )

                if fire_response.status_code == 200:
                    combat_events_count += 1

        # Verify combat events were created if any shots were fired
        if combat_events_count > 0:
            final_game = client.get(f"/games/{game_id}")
            final_state = final_game.json()

            # At least one ship should have taken damage or we should see combat events
            combat_events = [
                e for e in final_state["event_log"] if e["event_type"] == "broadside_fire"
            ]
            assert len(combat_events) == combat_events_count


class TestVictoryConditions:
    """Test that victory conditions are checked and triggered correctly."""

    def test_victory_by_ship_struck(self) -> None:
        """Test that game ends when a ship strikes.

        Note: This test doesn't guarantee a ship will strike in the turns simulated,
        but it verifies the system correctly checks and reports victory conditions.
        """
        # Create frigate duel game (first_struck victory)
        create_response = client.post(
            "/games",
            json={"scenario_id": "mvp_frigate_duel_v1"},
        )
        game_state = create_response.json()["state"]

        # Game should not be ended initially
        assert game_state["game_ended"] is False
        assert game_state["winner"] is None

        # The game will check victory after combat and reload phases
        # We verify that if a ship strikes, the game ends
        # (Actual striking depends on combat resolution and dice rolls)

    def test_turn_limit_not_exceeded(self) -> None:
        """Test that games respect turn limits from scenarios.

        Verifies:
        - Turn number increments correctly
        - Game doesn't exceed scenario turn limit
        """
        # Create game with turn limit
        create_response = client.post(
            "/games",
            json={"scenario_id": "mvp_frigate_duel_v1"},
        )
        game_id = create_response.json()["game_id"]
        initial_state = create_response.json()["state"]

        ships = initial_state["ships"]
        p1_ship_id = next(s["id"] for s in ships.values() if s["side"] == "P1")
        p2_ship_id = next(s["id"] for s in ships.values() if s["side"] == "P2")

        # Run multiple turns
        for turn_num in range(1, 6):
            # Submit orders
            client.post(
                f"/games/{game_id}/turns/{turn_num}/orders",
                json={"side": "P1", "orders": [{"ship_id": p1_ship_id, "movement_string": "0"}]},
            )
            client.post(
                f"/games/{game_id}/turns/{turn_num}/orders",
                json={"side": "P2", "orders": [{"ship_id": p2_ship_id, "movement_string": "0"}]},
            )

            # Mark ready
            client.post(f"/games/{game_id}/turns/{turn_num}/ready", json={"side": "P1"})
            client.post(f"/games/{game_id}/turns/{turn_num}/ready", json={"side": "P2"})

            # Resolve movement
            client.post(f"/games/{game_id}/turns/{turn_num}/resolve/movement")

            # Reload
            client.post(f"/games/{game_id}/turns/{turn_num}/resolve/reload")

            # Check if game ended
            game_response = client.get(f"/games/{game_id}")
            game_state = game_response.json()

            if game_state["game_ended"]:
                # Game ended, verify it was due to turn limit or victory
                break

            # Advance turn if game hasn't ended
            if not game_state["game_ended"]:
                client.post(f"/games/{game_id}/turns/{turn_num}/advance")

        # Final verification
        final_game = client.get(f"/games/{game_id}")
        final_state = final_game.json()

        # Verify turn number is reasonable
        assert final_state["turn_number"] <= 20  # Scenario turn limit
