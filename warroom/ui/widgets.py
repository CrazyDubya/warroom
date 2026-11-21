"""
Custom widgets for the War Room TUI.

These are the visual building blocks - witness panels, evidence boards,
whisper boxes, and more.
"""

from __future__ import annotations

from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, Input, Button, Label

from warroom.core import Evidence, Focus, FocusHealth, Hypothesis, WitnessType
from warroom.witnesses import Whisper, WitnessPanel


# Health icons
HEALTH_ICONS = {
    FocusHealth.NASCENT: ("🌱", "nascent"),
    FocusHealth.GROWING: ("🌿", "growing"),
    FocusHealth.BLOOMING: ("🌸", "blooming"),
    FocusHealth.STALLED: ("🥀", "stalled"),
    FocusHealth.DORMANT: ("💤", "dormant"),
    FocusHealth.RESOLVED: ("✓", "resolved"),
}

# Witness icons
WITNESS_ICONS = {
    WitnessType.CRITIC: "⚔",
    WitnessType.HISTORIAN: "📜",
    WitnessType.ARCHITECT: "📐",
    WitnessType.SHERLOCK: "🔍",
    WitnessType.GARDENER: "🌻",
    WitnessType.SCRIBE: "✒",
}


class FocusHeader(Static):
    """Header showing the current focus and session info."""

    focus: reactive[Focus | None] = reactive(None)
    witness_count: reactive[int] = reactive(0)
    session_time: reactive[str] = reactive("--:--")

    def render(self) -> RenderableType:
        if not self.focus:
            return Panel("No active focus", title="WAR ROOM", border_style="dim")

        health = self.focus.calculate_health()
        icon, _ = HEALTH_ICONS.get(health, ("?", "unknown"))

        title = f"FOCUS: {self.focus.name}"
        subtitle = f"WITNESSES: {self.witness_count} │ {self.session_time}"

        return Panel(
            Text(self.focus.question or "No question set", style="italic"),
            title=f"{icon} {title}",
            subtitle=subtitle,
            border_style="bold cyan",
        )


class WitnessBox(Static):
    """A box showing a single witness's current state and whisper."""

    DEFAULT_CSS = """
    WitnessBox {
        height: auto;
        min-height: 5;
        margin: 0 1;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        witness_type: WitnessType,
        whisper: Whisper | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.witness_type = witness_type
        self.whisper = whisper

    def render(self) -> RenderableType:
        icon = WITNESS_ICONS.get(self.witness_type, "?")
        name = self.witness_type.value.upper()

        if self.whisper:
            content = Text(self.whisper.message, style="italic")
            style = "yellow" if self.whisper.priority > 0.5 else "dim"
        else:
            content = Text("Observing...", style="dim italic")
            style = "dim"

        return Panel(
            content,
            title=f"{icon} {name}",
            border_style=style,
        )


class WitnessGrid(Container):
    """Grid of witness boxes."""

    DEFAULT_CSS = """
    WitnessGrid {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1;
        height: auto;
        min-height: 12;
    }
    """

    def __init__(self, focus: Focus | None = None, **kwargs):
        super().__init__(**kwargs)
        self.focus = focus

    async def update_focus(self, focus: Focus | None) -> None:
        """Rebuild existing child widgets when the displayed focus changes."""
        self.focus = focus
        await self.remove_children()
        await self.mount(*self.compose())

    def compose(self) -> ComposeResult:
        if not self.focus:
            yield Static("No focus selected", classes="dim")
            return

        panel = WitnessPanel(self.focus)
        whispers = {w.witness: w for w in panel.get_whispers(limit=4)}

        for wtype in self.focus.witnesses[:4]:
            yield WitnessBox(wtype, whispers.get(wtype))


class EvidenceItem(Static):
    """A single piece of evidence on the board."""

    DEFAULT_CSS = """
    EvidenceItem {
        height: 3;
        padding: 0 1;
        margin: 0 0 1 0;
    }

    EvidenceItem:hover {
        background: $surface;
    }
    """

    def __init__(self, evidence: Evidence, **kwargs):
        super().__init__(**kwargs)
        self.evidence = evidence

    def render(self) -> RenderableType:
        source_icon = {
            "user": "📌",
            "witness": "🔍",
            "memory": "💭",
            "external": "📎",
        }.get(self.evidence.source.value, "•")

        relevance_bar = "█" * int(self.evidence.relevance * 5) + "░" * (5 - int(self.evidence.relevance * 5))

        text = Text()
        text.append(f"{source_icon} ", style="bold")
        text.append(self.evidence.title, style="bold")
        text.append(f" [{relevance_bar}]", style="dim")

        if self.evidence.source_detail:
            text.append(f"\n   via {self.evidence.source_detail}", style="dim italic")

        return text


class EvidenceBoard(Container):
    """The shared evidence board."""

    DEFAULT_CSS = """
    EvidenceBoard {
        height: auto;
        min-height: 8;
        padding: 1;
        border: solid $primary;
    }
    """

    def __init__(self, focus: Focus | None = None, **kwargs):
        super().__init__(**kwargs)
        self.focus = focus

    async def update_focus(self, focus: Focus | None) -> None:
        """Rebuild existing child widgets when the displayed focus changes."""
        self.focus = focus
        await self.remove_children()
        await self.mount(*self.compose())

    def compose(self) -> ComposeResult:
        yield Static("══════════════ EVIDENCE BOARD ══════════════", classes="title")

        if not self.focus or not self.focus.evidence:
            yield Static("No evidence pinned yet. Add some!", classes="dim")
            return

        for evidence in self.focus.evidence[:5]:
            yield EvidenceItem(evidence)

        if len(self.focus.evidence) > 5:
            yield Static(
                f"  +{len(self.focus.evidence) - 5} more...",
                classes="dim",
            )


class HypothesisItem(Static):
    """A single hypothesis display."""

    def __init__(self, hypothesis: Hypothesis, **kwargs):
        super().__init__(**kwargs)
        self.hypothesis = hypothesis

    def render(self) -> RenderableType:
        icon = WITNESS_ICONS.get(self.hypothesis.witness, "?")
        conf = self.hypothesis.confidence
        conf_style = "green" if conf > 0.7 else "yellow" if conf > 0.4 else "dim"
        conf_bar = "●" * int(conf * 5) + "○" * (5 - int(conf * 5))

        text = Text()
        text.append(f"{icon} ", style="bold")
        text.append(f"[{conf_bar}] ", style=conf_style)
        text.append(self.hypothesis.statement[:60])
        if len(self.hypothesis.statement) > 60:
            text.append("...", style="dim")

        return text


class WhisperBar(Static):
    """The whisper bar at the bottom - ambient suggestions from witnesses."""

    DEFAULT_CSS = """
    WhisperBar {
        height: 3;
        padding: 0 2;
        background: $surface;
        border-top: solid $primary-darken-2;
    }
    """

    whisper: reactive[Whisper | None] = reactive(None)

    def render(self) -> RenderableType:
        if not self.whisper:
            return Text("Witnesses are observing...", style="dim italic")

        icon = WITNESS_ICONS.get(self.whisper.witness, "?")
        text = Text()
        text.append(f"{icon} ", style="bold")
        text.append(f"{self.whisper.witness.value.upper()}: ", style="bold cyan")
        text.append(f'"{self.whisper.message}"', style="italic")

        return text


class FocusList(Container):
    """List of all focuses for selection."""

    DEFAULT_CSS = """
    FocusList {
        height: 100%;
        padding: 1;
    }

    FocusList > Static {
        padding: 0 1;
    }

    FocusList > Static:hover {
        background: $surface;
    }
    """

    def __init__(self, focuses: list[Focus], **kwargs):
        super().__init__(**kwargs)
        self.focuses = focuses

    def compose(self) -> ComposeResult:
        yield Static("─ Active Focuses ─", classes="title")

        if not self.focuses:
            yield Static("No focuses yet. Create one!", classes="dim")
            return

        for focus in self.focuses:
            health = focus.calculate_health()
            icon, _ = HEALTH_ICONS.get(health, ("?", "unknown"))
            witness_count = len(focus.witnesses)
            evidence_count = len(focus.evidence)

            text = Text()
            text.append(f"{icon} ", style="bold")
            text.append(focus.name, style="bold")
            text.append(f" ({witness_count}w, {evidence_count}e)", style="dim")

            yield Static(text, id=f"focus-{focus.id}")


class CommandInput(Input):
    """The command input at the bottom."""

    DEFAULT_CSS = """
    CommandInput {
        dock: bottom;
        height: 3;
        border: none;
        background: $surface;
        padding: 0 2;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(placeholder="> Enter command or question...", **kwargs)


class StatusLine(Static):
    """Status line showing keybindings and mode."""

    DEFAULT_CSS = """
    StatusLine {
        dock: bottom;
        height: 1;
        background: $primary-darken-3;
        color: $text;
        padding: 0 2;
    }
    """

    mode: reactive[str] = reactive("war-room")

    def render(self) -> RenderableType:
        bindings = {
            "war-room": "[n]ew focus  [e]vidence  [w]itness  [/]search  [?]help  [q]uit",
            "lens-constellation": "[hjkl]navigate  [enter]focus  [esc]back  [/]search",
            "lens-river": "[j/k]scroll  [enter]dive  [esc]back  [t]oday",
            "lens-timeline": "[←/→]scroll  [enter]inspect  [esc]back",
            "theatre": "[esc]return  [tab]toggle agents  [e]vidence",
        }

        text = Text()
        text.append(f" {self.mode.upper()} ", style="reverse bold")
        text.append(" │ ", style="dim")
        text.append(bindings.get(self.mode, "[esc]back"), style="dim")

        return text
