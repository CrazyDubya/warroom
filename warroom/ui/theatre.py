"""
Theatre Mode - Deep Focus.

When you need to go deep on one thing. The world shrinks
to a single artifact. Agents whisper from below.
Everything else fades.
"""

from __future__ import annotations

from typing import Optional

from rich.console import RenderableType
from rich.panel import Panel
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from warroom.core import Evidence, Focus, Hypothesis, WitnessType
from warroom.witnesses import WitnessPanel, Whisper


WITNESS_ICONS = {
    WitnessType.CRITIC: "⚔",
    WitnessType.HISTORIAN: "📜",
    WitnessType.ARCHITECT: "📐",
    WitnessType.SHERLOCK: "🔍",
    WitnessType.GARDENER: "🌻",
    WitnessType.SCRIBE: "✒",
}


class TheatreHeader(Static):
    """The spotlight header in theatre mode."""

    DEFAULT_CSS = """
    TheatreHeader {
        height: 5;
        content-align: center middle;
        background: $surface;
        border-bottom: solid $primary;
    }
    """

    title: reactive[str] = reactive("DEEP FOCUS")
    subtitle: reactive[str] = reactive("")

    def render(self) -> RenderableType:
        text = Text()
        text.append("╔" + "═" * 40 + "╗\n", style="bold cyan")
        text.append("║", style="bold cyan")
        text.append(f"   D E E P   F O C U S   ", style="bold reverse")
        text.append(" " * 14 + "║\n", style="bold cyan")
        text.append("║", style="bold cyan")
        text.append(f"   {self.subtitle[:36]:^36}   ", style="dim")
        text.append("║\n", style="bold cyan")
        text.append("╚" + "═" * 40 + "╝", style="bold cyan")
        return text


class TheatreStage(Static):
    """The main stage where the focused content appears."""

    DEFAULT_CSS = """
    TheatreStage {
        height: 1fr;
        padding: 2 4;
        content-align: center middle;
    }
    """

    content: reactive[str] = reactive("")
    content_type: reactive[str] = reactive("text")

    def render(self) -> RenderableType:
        if not self.content:
            return Text("Nothing on stage. Select something to focus on.", style="dim")

        text = Text()

        # Add some theatrical framing
        text.append("\n")

        # Render the content with appropriate styling
        if self.content_type == "code":
            # Code gets a monospace treatment
            for line in self.content.split("\n"):
                text.append(f"       {line}\n", style="bright_white")
        elif self.content_type == "hypothesis":
            text.append("       💡 ", style="yellow")
            text.append(self.content + "\n", style="italic")
        elif self.content_type == "evidence":
            text.append("       📌 ", style="cyan")
            text.append(self.content + "\n")
        else:
            for line in self.content.split("\n"):
                text.append(f"       {line}\n")

        text.append("\n")

        return text


class TheatreWhisperBox(Static):
    """The whisper box below the stage."""

    DEFAULT_CSS = """
    TheatreWhisperBox {
        height: 5;
        padding: 1 4;
        background: $surface;
        border-top: solid $primary-darken-2;
    }
    """

    whisper: reactive[Whisper | None] = reactive(None)
    agents_visible: reactive[bool] = reactive(True)

    def render(self) -> RenderableType:
        if not self.agents_visible:
            return Text("(agents hidden - press [tab] to show)", style="dim italic")

        if not self.whisper:
            return Text("", style="dim")

        text = Text()
        text.append("    ┌" + "─" * 60 + "┐\n", style="dim")

        icon = WITNESS_ICONS.get(self.whisper.witness, "?")
        name = self.whisper.witness.value

        text.append("    │ ", style="dim")
        text.append(f"whisper: ", style="dim italic")
        text.append(f'"{self.whisper.message}"', style="italic")

        # Pad to fill the box
        msg_len = len(self.whisper.message) + 11
        padding = max(0, 58 - msg_len)
        text.append(" " * padding + " │\n", style="dim")

        text.append("    │ ", style="dim")
        text.append(f"— {icon} {name.upper()}", style="dim")
        text.append(" " * (57 - len(name)) + "│\n", style="dim")

        text.append("    └" + "─" * 60 + "┘", style="dim")

        return text


class TheatreControls(Static):
    """Minimal controls at the bottom."""

    DEFAULT_CSS = """
    TheatreControls {
        height: 1;
        padding: 0 2;
        background: $primary-darken-3;
    }
    """

    def render(self) -> RenderableType:
        text = Text()
        text.append(" THEATRE ", style="reverse bold")
        text.append(" │ ", style="dim")
        text.append("[ESC] return to war room  [tab] toggle agents  [e]vidence  [n]ext whisper", style="dim")
        return text


class TheatreMode(Container):
    """
    The Theatre - deep focus mode.

    Everything fades except the one thing you're focused on.
    Agents whisper from the shadows.
    """

    DEFAULT_CSS = """
    TheatreMode {
        layout: vertical;
        height: 100%;
        background: $background;
    }
    """

    def __init__(
        self,
        focus: Focus,
        target: Evidence | Hypothesis | str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.focus = focus
        self.target = target
        self.witness_panel = WitnessPanel(focus)
        self.agents_visible = True
        self.current_whisper_idx = 0

    def compose(self) -> ComposeResult:
        yield TheatreHeader()
        yield TheatreStage()
        yield TheatreWhisperBox()
        yield TheatreControls()

    def on_mount(self) -> None:
        """Set up the theatre when mounted."""
        header = self.query_one(TheatreHeader)
        stage = self.query_one(TheatreStage)
        whisper_box = self.query_one(TheatreWhisperBox)

        # Set header
        header.subtitle = self.focus.name

        # Set stage content
        if isinstance(self.target, Evidence):
            stage.content = self.target.content or self.target.title
            stage.content_type = "evidence"
        elif isinstance(self.target, Hypothesis):
            stage.content = self.target.statement
            stage.content_type = "hypothesis"
        elif isinstance(self.target, str):
            stage.content = self.target
            stage.content_type = "text"
        else:
            # Default to focus question or name
            stage.content = self.focus.question or self.focus.name
            stage.content_type = "text"

        # Get first whisper
        whispers = self.witness_panel.get_whispers()
        if whispers:
            whisper_box.whisper = whispers[0]

    def toggle_agents(self) -> None:
        """Toggle agent visibility."""
        self.agents_visible = not self.agents_visible
        whisper_box = self.query_one(TheatreWhisperBox)
        whisper_box.agents_visible = self.agents_visible

    def next_whisper(self) -> None:
        """Cycle to the next whisper."""
        whispers = self.witness_panel.get_whispers(limit=10)
        if whispers:
            self.current_whisper_idx = (self.current_whisper_idx + 1) % len(whispers)
            whisper_box = self.query_one(TheatreWhisperBox)
            whisper_box.whisper = whispers[self.current_whisper_idx]


class TheatreView(Static):
    """Static version of theatre for simple rendering."""

    def __init__(
        self,
        focus: Focus,
        target: Evidence | Hypothesis | str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.focus = focus
        self.target = target
        self.witness_panel = WitnessPanel(focus)

    def render(self) -> RenderableType:
        text = Text()

        # Header
        text.append("                    ╔" + "═" * 40 + "╗\n", style="bold cyan")
        text.append("                    ║", style="bold cyan")
        text.append("   D E E P   F O C U S   ", style="bold reverse")
        text.append(" " * 14 + "║\n", style="bold cyan")
        text.append("                    ║", style="bold cyan")
        subtitle = self.focus.name[:36]
        text.append(f"   {subtitle:^36}   ", style="dim")
        text.append("║\n", style="bold cyan")
        text.append("                    ╚" + "═" * 40 + "╝\n", style="bold cyan")
        text.append("                                      │\n", style="dim")
        text.append("                                      ▼\n", style="dim")

        # Stage frame
        text.append("┌" + "─" * 70 + "┐\n", style="dim")

        # Content
        if isinstance(self.target, Evidence):
            content = self.target.content or self.target.title
            icon = "📌"
        elif isinstance(self.target, Hypothesis):
            content = self.target.statement
            icon = "💡"
        else:
            content = str(self.target) if self.target else (self.focus.question or self.focus.name)
            icon = "◉"

        text.append("│" + " " * 70 + "│\n", style="dim")

        # Render content lines
        lines = content.split("\n")
        for line in lines[:8]:
            padded = f"  {icon} {line[:64]}"
            text.append("│", style="dim")
            text.append(f"{padded:<70}", style="bright_white")
            text.append("│\n", style="dim")
            icon = " "  # Only show icon on first line

        # Padding
        for _ in range(max(0, 6 - len(lines))):
            text.append("│" + " " * 70 + "│\n", style="dim")

        # Whisper
        whispers = self.witness_panel.get_whispers(limit=1)
        if whispers:
            whisper = whispers[0]
            w_icon = WITNESS_ICONS.get(whisper.witness, "?")
            w_name = whisper.witness.value.upper()
            w_msg = whisper.message[:55]

            text.append("│" + " " * 70 + "│\n", style="dim")
            text.append("│    ┌" + "─" * 62 + "┐   │\n", style="dim")
            text.append("│    │ ", style="dim")
            text.append(f'whisper: "{w_msg}"', style="italic")
            padding = 60 - len(w_msg) - 10
            text.append(" " * max(0, padding) + " │   │\n", style="dim")
            text.append("│    │ ", style="dim")
            text.append(f"— {w_icon} {w_name}", style="dim")
            text.append(" " * (59 - len(w_name)) + "│   │\n", style="dim")
            text.append("│    └" + "─" * 62 + "┘   │\n", style="dim")

        text.append("│" + " " * 70 + "│\n", style="dim")
        text.append("└" + "─" * 70 + "┘\n", style="dim")

        # Controls
        text.append("\n")
        text.append("          [ESC] return to war room    [tab] toggle agents\n", style="dim")

        return text
