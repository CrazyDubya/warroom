"""
River Lens - Temporal view of knowledge.

Shows knowledge organized by time, with recent items crisp
and old items compressed/faded. The river flows downward
into the depths of your past.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from rich.console import RenderableType
from rich.text import Text
from textual.widget import Widget
from textual.widgets import Static

from warroom.core import Evidence, Focus, Session, WarRoomState


class TimeBlock:
    """A block of time containing items."""

    def __init__(
        self,
        label: str,
        start: datetime,
        end: datetime,
        density: float = 1.0,
    ):
        self.label = label
        self.start = start
        self.end = end
        self.density = density  # 1.0 = full detail, 0.0 = maximally compressed
        self.items: list[tuple[str, str, datetime]] = []  # (type, description, time)

    def add_item(self, item_type: str, description: str, time: datetime) -> None:
        """Add an item to this time block."""
        if self.start <= time <= self.end:
            self.items.append((item_type, description, time))

    def render(self, width: int = 70) -> Text:
        """Render this time block."""
        text = Text()

        # Density determines visual style
        if self.density > 0.8:
            fill = "░"
            style = "white"
        elif self.density > 0.5:
            fill = "▒"
            style = "bright_white"
        elif self.density > 0.2:
            fill = "▓"
            style = "dim"
        else:
            fill = "█"
            style = "dim"

        # Header line
        header = f" {self.label} "
        padding = fill * ((width - len(header)) // 2)
        text.append(f"{padding}{header}{padding}\n", style=style)

        # Items (compressed based on density)
        items_to_show = int(max(1, len(self.items) * self.density))
        for item_type, desc, _ in self.items[:items_to_show]:
            icon = {"evidence": "→", "session": "◆", "hypothesis": "◇"}.get(
                item_type, "•"
            )
            # Truncate based on density
            max_len = int(50 * self.density) + 20
            if len(desc) > max_len:
                desc = desc[: max_len - 3] + "..."
            text.append(f"{fill}{fill} {icon} {desc}\n", style=style)

        # Show count if items hidden
        hidden = len(self.items) - items_to_show
        if hidden > 0:
            text.append(f"{fill}{fill}   +{hidden} more...\n", style="dim")

        # Footer
        text.append(fill * width + "\n", style=style)

        return text


class RiverView(Static):
    """The river view widget."""

    DEFAULT_CSS = """
    RiverView {
        height: 100%;
        padding: 1;
        overflow-y: auto;
    }
    """

    def __init__(
        self,
        state: WarRoomState,
        current_focus: Optional[Focus] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.state = state
        self.current_focus = current_focus
        self.blocks = self._build_time_blocks()

    def _build_time_blocks(self) -> list[TimeBlock]:
        """Build time blocks from the current focus or all focuses."""
        now = datetime.now()
        blocks = []

        # Define time periods with decreasing density
        periods = [
            ("TODAY", now - timedelta(days=1), now, 1.0),
            ("YESTERDAY", now - timedelta(days=2), now - timedelta(days=1), 0.9),
            ("THIS WEEK", now - timedelta(days=7), now - timedelta(days=2), 0.7),
            ("LAST WEEK", now - timedelta(days=14), now - timedelta(days=7), 0.5),
            ("THIS MONTH", now - timedelta(days=30), now - timedelta(days=14), 0.3),
            ("OLDER", now - timedelta(days=365), now - timedelta(days=30), 0.15),
            ("DEEP TIME", now - timedelta(days=3650), now - timedelta(days=365), 0.05),
        ]

        for label, start, end, density in periods:
            block = TimeBlock(label, start, end, density)

            # Collect items from focus or all focuses
            focuses = [self.current_focus] if self.current_focus else self.state.focuses

            for focus in focuses:
                if not focus:
                    continue

                # Add evidence
                for evidence in focus.evidence:
                    block.add_item(
                        "evidence",
                        f"{evidence.title} ({focus.name})",
                        evidence.pinned_at,
                    )

                # Add sessions
                for session in focus.sessions:
                    desc = f"Session on {focus.name}"
                    if session.notes:
                        desc += f": {session.notes[:30]}"
                    block.add_item("session", desc, session.started_at)

                # Add hypotheses
                for hyp in focus.hypotheses:
                    block.add_item(
                        "hypothesis",
                        f"{hyp.witness.value}: {hyp.statement[:40]}",
                        hyp.created_at,
                    )

            # Only include blocks with items
            if block.items:
                blocks.append(block)

        return blocks

    def render(self) -> RenderableType:
        text = Text()

        # Header
        text.append("WAR ROOM > RIVER LENS", style="bold cyan")
        text.append("                         [ESC to return]\n", style="dim")

        if self.current_focus:
            text.append(f"FOCUS: {self.current_focus.name}\n", style="bold")
        text.append("═" * 70 + "\n\n", style="dim")

        # Render time blocks
        if not self.blocks:
            text.append("\nThe river is empty. No history yet.\n", style="dim italic")
            text.append("Start a session, add evidence, let time flow...\n", style="dim")
        else:
            for block in self.blocks:
                text.append_text(block.render())
                text.append("\n")

        # Footer
        text.append("\n")
        text.append("[j/k] scroll  [enter] dive  [t]oday  ", style="dim")

        return text


class RiverLens:
    """The River lens - temporal view of knowledge."""

    name = "river"
    description = "Knowledge organized by time, flowing into the past"

    def __init__(self, state: WarRoomState):
        self.state = state

    def create_view(self, current_focus: Optional[Focus] = None) -> Widget:
        """Create the river view widget."""
        return RiverView(self.state, current_focus)
