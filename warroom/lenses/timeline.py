"""
Timeline Lens - Causal history of an artifact.

Shows the biography of a focus - how it came to be,
what influenced it, key moments in its development.
This is the archaeological view.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from rich.console import RenderableType
from rich.text import Text
from textual.widget import Widget
from textual.widgets import Static

from warroom.core import Evidence, Focus, Hypothesis, Session, WarRoomState


@dataclass
class TimelineEvent:
    """A single event on the timeline."""
    time: datetime
    label: str
    description: str
    event_type: str  # birth, evidence, hypothesis, session, milestone
    source: Optional[str] = None  # Who/what created this event
    is_significant: bool = False


class TimelineView(Static):
    """The timeline view widget."""

    DEFAULT_CSS = """
    TimelineView {
        height: 100%;
        padding: 1;
    }
    """

    def __init__(
        self,
        focus: Focus,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.focus = focus
        self.events = self._build_events()
        self.viewport_start = 0
        self.viewport_width = 70

    def _build_events(self) -> list[TimelineEvent]:
        """Build timeline events from the focus."""
        events = []

        # Birth event
        events.append(TimelineEvent(
            time=self.focus.created_at,
            label="BIRTH",
            description=f"Focus '{self.focus.name}' created",
            event_type="birth",
            is_significant=True,
        ))

        # Evidence events
        for evidence in self.focus.evidence:
            events.append(TimelineEvent(
                time=evidence.pinned_at,
                label=evidence.title[:15],
                description=evidence.content[:50] if evidence.content else "",
                event_type="evidence",
                source=evidence.source_detail or evidence.source.value,
            ))

        # Hypothesis events
        for hyp in self.focus.hypotheses:
            events.append(TimelineEvent(
                time=hyp.created_at,
                label=f"HYPOTHESIS",
                description=hyp.statement[:50],
                event_type="hypothesis",
                source=hyp.witness.value.upper(),
                is_significant=hyp.confidence > 0.7,
            ))

        # Session events
        for session in self.focus.sessions:
            duration = session.duration_minutes or 0
            events.append(TimelineEvent(
                time=session.started_at,
                label=f"SESSION ({duration}m)",
                description=session.notes[:50] if session.notes else "Work session",
                event_type="session",
            ))

        # Sort by time
        events.sort(key=lambda e: e.time)

        return events

    def render(self) -> RenderableType:
        text = Text()

        # Header
        text.append("WAR ROOM > TIMELINE LENS", style="bold cyan")
        text.append("                      [ESC to return]\n", style="dim")
        text.append(f"BIOGRAPHY OF: {self.focus.name}\n", style="bold")
        text.append("═" * 70 + "\n\n", style="dim")

        if not self.events:
            text.append("No history yet. The timeline is empty.\n", style="dim italic")
            return text

        # Calculate timeline positions
        if len(self.events) == 1:
            positions = [35]
        else:
            min_time = self.events[0].time
            max_time = self.events[-1].time
            time_range = (max_time - min_time).total_seconds() or 1

            positions = []
            for event in self.events:
                offset = (event.time - min_time).total_seconds()
                pos = int((offset / time_range) * 60) + 5
                positions.append(pos)

        # Draw the timeline
        # Top labels (alternating above/below to avoid overlap)
        for i, (event, pos) in enumerate(zip(self.events, positions)):
            if i % 2 == 0:  # Above the line
                # Pad to position
                text.append(" " * pos)
                label = event.label[:12]
                text.append(f"{label}\n", style="bold" if event.is_significant else "")

        # The main timeline
        line = list("─" * 70)
        for i, pos in enumerate(positions):
            if 0 <= pos < 70:
                if self.events[i].is_significant:
                    line[pos] = "●"
                else:
                    line[pos] = "○"

        # Add markers
        line[0] = "├"
        line[-1] = "┤"

        text.append("".join(line) + "\n", style="cyan")

        # Below the line - show details
        for i, (event, pos) in enumerate(zip(self.events, positions)):
            if i % 2 == 1:  # Below the line
                text.append(" " * pos + "│\n", style="dim")
                text.append(" " * pos)
                text.append(f"{event.label[:12]}\n", style="bold" if event.is_significant else "")

        text.append("\n")

        # Event details section
        text.append("─" * 70 + "\n", style="dim")
        text.append(" EVENTS:\n", style="bold")

        for event in self.events:
            icon = {
                "birth": "◆",
                "evidence": "📌",
                "hypothesis": "💡",
                "session": "⏱",
                "milestone": "★",
            }.get(event.event_type, "•")

            time_str = event.time.strftime("%Y-%m-%d %H:%M")
            style = "bold cyan" if event.is_significant else ""

            text.append(f" {icon} ", style=style)
            text.append(f"[{time_str}] ", style="dim")
            text.append(f"{event.label}", style=style)

            if event.source:
                text.append(f" (via {event.source})", style="dim")

            text.append("\n")

            if event.description:
                text.append(f"    {event.description[:60]}\n", style="dim italic")

        text.append("\n")
        text.append("[←/→] scroll  [enter] inspect  [h]ypothesis  ", style="dim")

        return text


class TimelineLens:
    """The Timeline lens - causal history of a focus."""

    name = "timeline"
    description = "The biography of a focus - how it came to be"

    def __init__(self, state: WarRoomState):
        self.state = state

    def create_view(self, focus: Focus) -> Widget:
        """Create the timeline view widget."""
        return TimelineView(focus)
