"""
War Room - The Main Application.

A collaborative investigation environment where you and AI witnesses
work together to explore, debug, design, and understand.

The War Room is the center. Everything else supports it.
"""

from __future__ import annotations

import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static

from warroom.core import (
    Evidence,
    EvidenceSource,
    Focus,
    FocusHealth,
    StateManager,
    WarRoomState,
    WitnessType,
)
from warroom.lenses import ConstellationLens, RiverLens, TimelineLens
from warroom.ui import (
    EvidenceBoard,
    FocusHeader,
    FocusList,
    StatusLine,
    TheatreView,
    WhisperBar,
    WitnessGrid,
)
from warroom.witnesses import WitnessPanel


class Mode(str, Enum):
    """Current mode of the War Room."""
    WAR_ROOM = "war-room"
    CONSTELLATION = "lens-constellation"
    RIVER = "lens-river"
    TIMELINE = "lens-timeline"
    THEATRE = "theatre"
    GARDEN = "garden"


class WarRoomApp(App):
    """The War Room application."""

    TITLE = "WAR ROOM"
    SUB_TITLE = "Collaborative Investigation Environment"

    CSS = """
    Screen {
        background: $background;
    }

    #main-container {
        layout: grid;
        grid-size: 2 2;
        grid-columns: 1fr 1fr;
        grid-rows: auto 1fr;
        height: 100%;
        padding: 0;
    }

    #focus-header {
        column-span: 2;
        height: auto;
        min-height: 5;
    }

    #witness-section {
        height: 100%;
        padding: 1;
    }

    #evidence-section {
        height: 100%;
        padding: 1;
    }

    #sidebar {
        width: 25;
        height: 100%;
        border-right: solid $primary-darken-2;
    }

    #content {
        height: 100%;
    }

    #whisper-bar {
        dock: bottom;
        height: 3;
    }

    #status-line {
        dock: bottom;
        height: 1;
    }

    #command-input {
        dock: bottom;
        height: 3;
    }

    .title {
        text-style: bold;
        color: $primary;
        padding: 0 1;
    }

    .dim {
        color: $text-muted;
    }

    #lens-view {
        height: 100%;
        padding: 1;
    }

    #theatre-view {
        height: 100%;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("n", "new_focus", "New Focus"),
        Binding("e", "add_evidence", "Add Evidence"),
        Binding("w", "manage_witnesses", "Witnesses"),
        Binding("c", "lens_constellation", "Constellation"),
        Binding("r", "lens_river", "River"),
        Binding("t", "lens_timeline", "Timeline"),
        Binding("d", "theatre", "Deep Focus"),
        Binding("g", "garden", "Garden"),
        Binding("escape", "back", "Back"),
        Binding("?", "help", "Help"),
    ]

    mode: reactive[Mode] = reactive(Mode.WAR_ROOM)
    state: reactive[WarRoomState] = reactive(WarRoomState)

    def __init__(self, state_path: Optional[Path] = None):
        super().__init__()
        self.state_manager = StateManager(state_path)
        self.state = self.state_manager.load()

        # Create a demo focus if none exist
        if not self.state.focuses:
            self._create_demo_data()

    def _create_demo_data(self) -> None:
        """Create demo data for first run."""
        # Create a demo focus
        focus = self.state.create_focus(
            name="War Room Development",
            question="How do we build the ultimate collaborative investigation TUI?",
        )
        focus.witnesses = [
            WitnessType.CRITIC,
            WitnessType.HISTORIAN,
            WitnessType.ARCHITECT,
            WitnessType.SHERLOCK,
        ]
        focus.tags = ["tui", "collaboration", "ai"]

        # Add some evidence
        focus.add_evidence(
            title="Core architecture defined",
            content="Focus → Witnesses → Evidence → Lenses",
            source=EvidenceSource.USER,
        )
        focus.add_evidence(
            title="Textual framework chosen",
            content="Modern Python TUI with async support",
            source=EvidenceSource.USER,
        )

        # Add a hypothesis
        focus.add_hypothesis(
            witness=WitnessType.ARCHITECT,
            statement="A modular lens system will enable multiple views of the same data",
            confidence=0.75,
        )

        # Start a session
        session = focus.start_session()
        session.notes = "Initial development session"

        # Create a second focus
        focus2 = self.state.create_focus(
            name="Auth Bug Investigation",
            question="Why does the session expire unexpectedly?",
        )
        focus2.witnesses = [WitnessType.SHERLOCK, WitnessType.HISTORIAN]
        focus2.tags = ["bug", "auth"]

        focus2.add_evidence(
            title="Stack trace captured",
            content="NullPointerException at session.validate()",
            source=EvidenceSource.USER,
        )

        focus2.add_hypothesis(
            witness=WitnessType.SHERLOCK,
            statement="Race condition between token refresh and validation",
            confidence=0.67,
            supporting_evidence=[focus2.evidence[0].id],
        )

        # Set first focus as active
        self.state.active_focus_id = focus.id

    def compose(self) -> ComposeResult:
        """Create the application layout."""
        yield Header()

        with Container(id="main-container"):
            yield FocusHeader(id="focus-header")

            with Container(id="witness-section"):
                yield Static("WITNESSES", classes="title")
                yield WitnessGrid(id="witness-grid")

            with Container(id="evidence-section"):
                yield EvidenceBoard(id="evidence-board")

        yield WhisperBar(id="whisper-bar")
        yield Input(placeholder="> Enter command or question...", id="command-input")
        yield StatusLine(id="status-line")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the application."""
        self._update_display()

    def _update_display(self) -> None:
        """Update all display elements based on current state."""
        focus = self.state.active_focus

        # Update header
        header = self.query_one("#focus-header", FocusHeader)
        header.focus = focus
        if focus:
            header.witness_count = len(focus.witnesses)

        # Update witness grid
        witness_grid = self.query_one("#witness-grid", WitnessGrid)
        witness_grid.call_later(witness_grid.update_focus, focus)

        # Update evidence board
        evidence_board = self.query_one("#evidence-board", EvidenceBoard)
        evidence_board.call_later(evidence_board.update_focus, focus)

        # Update whisper bar
        whisper_bar = self.query_one("#whisper-bar", WhisperBar)
        if focus:
            panel = WitnessPanel(focus)
            whispers = panel.get_whispers(limit=1)
            if whispers:
                whisper_bar.whisper = whispers[0]

        # Update status line
        status = self.query_one("#status-line", StatusLine)
        status.mode = self.mode.value

        # Refresh widgets
        self.refresh()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command input."""
        command = event.value.strip()
        event.input.value = ""

        if not command:
            return

        focus = self.state.active_focus

        # Parse commands
        if command.startswith("/"):
            await self._handle_command(command[1:])
        elif command.startswith("+"):
            # Quick add evidence
            if focus:
                focus.add_evidence(
                    title=command[1:].strip(),
                    content="",
                    source=EvidenceSource.USER,
                )
                self._update_display()
        elif command.startswith("?"):
            # Set focus question
            if focus:
                focus.question = command[1:].strip()
                self._update_display()
        else:
            # Treat as note/thinking
            if focus:
                focus.add_evidence(
                    title=f"Note: {command[:30]}...",
                    content=command,
                    source=EvidenceSource.USER,
                )
                self._update_display()

        # Save state
        self.state_manager.save(self.state)

    async def _handle_command(self, cmd: str) -> None:
        """Handle slash commands."""
        parts = cmd.split(maxsplit=1)
        if not parts:
            return
        action = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if action == "new":
            focus = self.state.create_focus(name=args or "New Focus")
            self._update_display()
        elif action == "focus":
            # Switch focus by name
            for f in self.state.focuses:
                if args.lower() in f.name.lower():
                    self.state.active_focus_id = f.id
                    self._update_display()
                    break
        elif action == "witness":
            # Add a witness
            if self.state.active_focus:
                wtype = args.upper()
                if hasattr(WitnessType, wtype):
                    self.state.active_focus.witnesses.append(WitnessType[wtype])
                    self._update_display()
        elif action == "hypothesis":
            # Generate hypotheses
            if self.state.active_focus:
                panel = WitnessPanel(self.state.active_focus)
                for hyp in panel.generate_hypotheses():
                    self.state.active_focus.hypotheses.append(hyp)
                self._update_display()
        elif action == "save":
            self.state_manager.save(self.state)
        elif action == "help":
            self.action_help()

    def action_new_focus(self) -> None:
        """Create a new focus."""
        focus = self.state.create_focus(name=f"Focus {len(self.state.focuses) + 1}")
        self.state_manager.save(self.state)
        self._update_display()

    def action_add_evidence(self) -> None:
        """Prompt to add evidence."""
        # In a full implementation, this would open a modal
        pass

    def action_manage_witnesses(self) -> None:
        """Manage witnesses for the current focus."""
        pass

    def action_lens_constellation(self) -> None:
        """Switch to constellation lens."""
        self.mode = Mode.CONSTELLATION
        self._show_lens("constellation")

    def action_lens_river(self) -> None:
        """Switch to river lens."""
        self.mode = Mode.RIVER
        self._show_lens("river")

    def action_lens_timeline(self) -> None:
        """Switch to timeline lens."""
        self.mode = Mode.TIMELINE
        self._show_lens("timeline")

    def action_theatre(self) -> None:
        """Enter theatre mode."""
        self.mode = Mode.THEATRE
        self._show_theatre()

    def action_garden(self) -> None:
        """Show garden view."""
        self.mode = Mode.GARDEN
        self._update_display()

    def action_back(self) -> None:
        """Go back to war room."""
        self.mode = Mode.WAR_ROOM
        self._update_display()

    def action_help(self) -> None:
        """Show help."""
        pass

    def _show_lens(self, lens_name: str) -> None:
        """Show a lens view."""
        # In a full implementation, this would swap the main container
        self._update_display()

    def _show_theatre(self) -> None:
        """Show theatre mode."""
        # In a full implementation, this would replace the entire screen
        self._update_display()


def main() -> None:
    """Entry point for the War Room application."""
    app = WarRoomApp()
    app.run()


# Also provide a demo mode that prints to console without full TUI
def demo() -> None:
    """Run a demo showing the War Room concepts."""
    console = Console()

    # Create state
    state = WarRoomState()

    # Create demo focus
    focus = state.create_focus(
        name="API Design",
        question="How should we structure the new API?",
    )
    focus.witnesses = [
        WitnessType.CRITIC,
        WitnessType.HISTORIAN,
        WitnessType.ARCHITECT,
        WitnessType.SHERLOCK,
    ]

    focus.add_evidence(
        title="REST vs GraphQL notes",
        content="Considered both approaches. REST is simpler for our use case.",
        source=EvidenceSource.USER,
    )
    focus.add_evidence(
        title="Competitor API analysis",
        content="Most competitors use REST with JWT auth.",
        source=EvidenceSource.WITNESS,
        source_detail="HISTORIAN",
    )

    focus.add_hypothesis(
        witness=WitnessType.ARCHITECT,
        statement="A gateway pattern will decouple auth from business logic",
        confidence=0.72,
    )
    focus.add_hypothesis(
        witness=WitnessType.CRITIC,
        statement="JWT refresh tokens add complexity - consider alternatives",
        confidence=0.55,
    )

    # Get witnesses
    panel = WitnessPanel(focus)
    whispers = panel.get_whispers(limit=4)

    # Render War Room
    console.print()
    console.print(Panel(
        f"[bold]{focus.name}[/bold]\n[italic]{focus.question}[/italic]",
        title="[bold cyan]FOCUS[/bold cyan]",
        subtitle=f"WITNESSES: {len(focus.witnesses)} │ Session 1",
        border_style="cyan",
    ))
    console.print()

    # Witness grid
    console.print("[bold]WITNESSES[/bold]")
    console.print("─" * 70)

    for i, wtype in enumerate(focus.witnesses):
        whisper = next((w for w in whispers if w.witness == wtype), None)
        icon = {"critic": "⚔", "historian": "📜", "architect": "📐", "sherlock": "🔍"}.get(wtype.value, "?")

        msg = whisper.message if whisper else "Observing..."
        console.print(f"  {icon} [bold]{wtype.value.upper():12}[/bold] │ [italic]{msg[:45]}[/italic]")

    console.print()

    # Evidence board
    console.print("[bold]EVIDENCE BOARD[/bold]")
    console.print("═" * 70)
    for evidence in focus.evidence:
        icon = "📌" if evidence.source == EvidenceSource.USER else "🔍"
        console.print(f"  {icon} [bold]{evidence.title}[/bold]")
        if evidence.source_detail:
            console.print(f"      [dim]via {evidence.source_detail}[/dim]")
    console.print()

    # Hypotheses
    console.print("[bold]HYPOTHESES[/bold]")
    console.print("─" * 70)
    for hyp in focus.hypotheses:
        conf = hyp.confidence
        conf_bar = "●" * int(conf * 5) + "○" * (5 - int(conf * 5))
        icon = {"critic": "⚔", "architect": "📐", "sherlock": "🔍"}.get(hyp.witness.value, "?")
        style = "green" if conf > 0.7 else "yellow" if conf > 0.4 else "dim"
        console.print(f"  {icon} [{style}]{conf_bar}[/{style}] {hyp.statement[:55]}...")
    console.print()

    # Whisper bar
    if whispers:
        w = whispers[0]
        icon = {"critic": "⚔", "historian": "📜", "architect": "📐", "sherlock": "🔍"}.get(w.witness.value, "?")
        console.print(Panel(
            f'{icon} [bold cyan]{w.witness.value.upper()}[/bold cyan]: [italic]"{w.message}"[/italic]',
            border_style="dim",
        ))

    console.print()
    console.print("[dim][n]ew focus  [e]vidence  [c]onstellation  [r]iver  [t]imeline  [d]eep focus  [q]uit[/dim]")
    console.print()

    # Show lenses
    console.print("\n" + "=" * 70)
    console.print("[bold cyan]LENSES AVAILABLE[/bold cyan]")
    console.print("=" * 70 + "\n")

    # Constellation preview
    console.print("[bold]CONSTELLATION[/bold] - Spatial view of knowledge")
    lens = ConstellationLens(state)
    view = lens.create_view(focus)
    console.print(view.render())

    # River preview
    console.print("\n[bold]RIVER[/bold] - Temporal view of knowledge")
    lens = RiverLens(state)
    view = lens.create_view(focus)
    console.print(view.render())

    # Timeline preview
    console.print("\n[bold]TIMELINE[/bold] - Causal history")
    lens = TimelineLens(state)
    view = lens.create_view(focus)
    console.print(view.render())

    # Theatre preview
    console.print("\n[bold]THEATRE[/bold] - Deep focus mode")
    theatre = TheatreView(focus, focus.hypotheses[0] if focus.hypotheses else None)
    console.print(theatre.render())


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        main()
