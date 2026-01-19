"""Event log management system for audit trail and debugging."""

from pydantic import BaseModel, Field

from ..models.common import GamePhase
from ..models.events import EventLogEntry


class EventLog(BaseModel):
    """Container for game event log entries.

    Stores events chronologically for debugging, replay, and audit trail.
    """

    entries: list[EventLogEntry] = Field(
        default_factory=list,
        description="Chronologically ordered list of event log entries",
    )

    def add_event(self, event: EventLogEntry) -> None:
        """Add a single event to the log.

        Args:
            event: EventLogEntry to add
        """
        self.entries.append(event)

    def add_events(self, events: list[EventLogEntry]) -> None:
        """Add multiple events to the log.

        Args:
            events: List of EventLogEntry objects to add
        """
        self.entries.extend(events)

    def get_all_events(self) -> list[EventLogEntry]:
        """Get all events in chronological order.

        Returns:
            List of all EventLogEntry objects
        """
        return self.entries.copy()

    def get_events_for_turn(self, turn_number: int) -> list[EventLogEntry]:
        """Get all events for a specific turn.

        Args:
            turn_number: Turn number to filter by

        Returns:
            List of events from the specified turn
        """
        return [e for e in self.entries if e.turn_number == turn_number]

    def get_events_for_phase(self, turn_number: int, phase: GamePhase) -> list[EventLogEntry]:
        """Get all events for a specific turn and phase.

        Args:
            turn_number: Turn number to filter by
            phase: Game phase to filter by

        Returns:
            List of events from the specified turn and phase
        """
        return [e for e in self.entries if e.turn_number == turn_number and e.phase == phase]

    def get_events_by_type(self, event_type: str) -> list[EventLogEntry]:
        """Get all events of a specific type.

        Args:
            event_type: Event type to filter by (e.g., 'collision', 'firing')

        Returns:
            List of events matching the type
        """
        return [e for e in self.entries if e.event_type == event_type]

    def get_recent_events(self, count: int) -> list[EventLogEntry]:
        """Get the most recent N events.

        Args:
            count: Number of recent events to retrieve

        Returns:
            List of the most recent events (up to count)
        """
        return self.entries[-count:] if count > 0 else []

    def clear(self) -> None:
        """Clear all events from the log.

        Useful for testing or starting fresh.
        """
        self.entries.clear()

    def event_count(self) -> int:
        """Get the total number of events in the log.

        Returns:
            Number of events currently stored
        """
        return len(self.entries)

    def get_turn_summary(self, turn_number: int) -> dict[GamePhase, int]:
        """Get a summary of event counts by phase for a specific turn.

        Args:
            turn_number: Turn number to summarize

        Returns:
            Dictionary mapping GamePhase to event count for that phase
        """
        summary: dict[GamePhase, int] = {}
        for event in self.entries:
            if event.turn_number == turn_number:
                summary[event.phase] = summary.get(event.phase, 0) + 1
        return summary

    def has_events_for_turn(self, turn_number: int) -> bool:
        """Check if there are any events for a specific turn.

        Args:
            turn_number: Turn number to check

        Returns:
            True if at least one event exists for this turn
        """
        return any(e.turn_number == turn_number for e in self.entries)
