"""Dendrite - A TUI for growing ideas through time."""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Input, Static, Label
from textual.css.query import NoMatches

from .models import Forest, Tree, Node, NodeState
from .widgets import IdeaTreeWidget, TimelineWidget, NodeDetailWidget, ContextInputWidget


class InputModal(ModalScreen[str]):
    """A modal for text input."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    CSS = """
    InputModal {
        align: center middle;
    }

    InputModal > Container {
        width: 60;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    InputModal Input {
        width: 100%;
        margin: 1 0;
    }

    InputModal .title {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1;
    }

    InputModal .hint {
        text-align: center;
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(self, title: str, placeholder: str = "", hint: str = ""):
        super().__init__()
        self.title_text = title
        self.placeholder = placeholder
        self.hint_text = hint

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(self.title_text, classes="title")
            yield Input(placeholder=self.placeholder)
            if self.hint_text:
                yield Label(self.hint_text, classes="hint")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.value.strip():
            self.dismiss(event.value.strip())

    def action_cancel(self) -> None:
        self.dismiss("")


class ContextModal(ModalScreen[str]):
    """A modal for adding context to an action."""

    BINDINGS = [
        Binding("escape", "skip", "Skip"),
        Binding("enter", "submit", "Submit", show=False),
    ]

    CSS = """
    ContextModal {
        align: center middle;
    }

    ContextModal > Container {
        width: 70;
        height: auto;
        border: thick $warning;
        background: $surface;
        padding: 1 2;
    }

    ContextModal Input {
        width: 100%;
        margin: 1 0;
    }

    ContextModal .title {
        text-align: center;
        text-style: bold;
        color: $warning;
        padding: 1;
    }

    ContextModal .subtitle {
        text-align: center;
        color: $text-muted;
        text-style: italic;
        padding-bottom: 1;
    }
    """

    def __init__(self, action: str):
        super().__init__()
        self.action = action

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("What's the context?", classes="title")
            yield Label(f"Why are you {self.action}? What triggered this thought?", classes="subtitle")
            yield Input(placeholder="Optional: capture the moment...")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip())

    def action_skip(self) -> None:
        self.dismiss("")


class DendriteApp(App):
    """The main Dendrite application."""

    TITLE = "Dendrite"
    SUB_TITLE = "Grow your ideas through time"

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        width: 100%;
        height: 100%;
    }

    #left-panel {
        width: 45%;
        height: 100%;
        border-right: solid $primary;
    }

    #right-panel {
        width: 55%;
        height: 100%;
    }

    #tree-container {
        height: 70%;
        border-bottom: solid $primary-darken-2;
    }

    #timeline-container {
        height: 30%;
        padding: 1;
    }

    #detail-container {
        height: 70%;
        padding: 1;
        border-bottom: solid $primary-darken-2;
    }

    #context-container {
        height: 30%;
        padding: 1;
    }

    IdeaTreeWidget {
        padding: 1;
    }

    TimelineWidget {
        height: 100%;
    }

    NodeDetailWidget {
        height: 100%;
    }

    ContextInputWidget {
        height: 100%;
        content-align: center middle;
    }

    .panel-title {
        dock: top;
        padding: 0 1;
        background: $primary-darken-2;
        color: $text;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("n", "new_seed", "New Seed"),
        Binding("b", "branch", "Branch"),
        Binding("e", "edit", "Edit"),
        Binding("g", "grow", "Grow"),
        Binding("p", "prune", "Prune"),
        Binding("d", "dormant", "Dormant"),
        Binding("t", "toggle_timeline", "Timeline"),
        Binding("?", "help", "Help"),
    ]

    def __init__(self):
        super().__init__()
        self.forest = Forest()
        # Create an initial tree
        self.active_tree = self.forest.create_tree("My Ideas")

        # Add some demo content
        self._seed_demo_data()

    def _seed_demo_data(self) -> None:
        """Add some initial demo ideas to explore."""
        root = self.active_tree.add_node(
            "TUI Framework Ideas",
            context="Starting to think about terminal interfaces"
        )
        root.set_state(NodeState.GROWING)

        child1 = self.active_tree.branch(
            root.id,
            "Tree-based navigation",
            context="Everything is a tree - files, ideas, time"
        )
        child1.set_state(NodeState.SPROUTING)

        self.active_tree.branch(
            child1.id,
            "Collapsible branches like lazygit",
            context="Users love the lazygit UX"
        )

        self.active_tree.branch(
            child1.id,
            "Keyboard-driven with vim bindings",
            context="Our users live in the terminal"
        )

        child2 = self.active_tree.branch(
            root.id,
            "Temporal awareness",
            context="Time is a first-class concept"
        )
        child2.set_state(NodeState.SPROUTING)

        self.active_tree.branch(
            child2.id,
            "Show history as a timeline",
            context="Every change should be visible"
        )

        child3 = self.active_tree.branch(
            root.id,
            "Context capture",
            context="Why did I think this? I always forget"
        )

        self.active_tree.branch(
            child3.id,
            "Prompt for context on each action",
            context="Make it optional but encouraged"
        )

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            with Vertical(id="left-panel"):
                with Container(id="tree-container"):
                    yield Label("🌳 Ideas", classes="panel-title")
                    yield IdeaTreeWidget(self.active_tree, id="idea-tree")
                with Container(id="timeline-container"):
                    yield Label("⏱ Timeline", classes="panel-title")
                    yield TimelineWidget(id="timeline")
            with Vertical(id="right-panel"):
                with Container(id="detail-container"):
                    yield Label("📋 Details", classes="panel-title")
                    yield NodeDetailWidget(id="node-detail")
                with Container(id="context-container"):
                    yield Label("💡 Context", classes="panel-title")
                    yield ContextInputWidget(id="context-hint")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app state after mounting."""
        tree_widget = self.query_one("#idea-tree", IdeaTreeWidget)
        tree_widget.set_tree(self.active_tree)
        tree_widget.root.expand_all()

        self._update_timeline()
        self._update_context_hint("Navigate with arrows. Press 'n' for new seed, 'b' to branch.")

    def on_tree_node_selected(self, event: IdeaTreeWidget.NodeSelected) -> None:
        """Handle node selection in the tree."""
        if event.node.data:
            node_id = event.node.data
            node = self.active_tree.get_node(node_id)
            if node:
                path = self.active_tree.get_path_to_root(node_id)
                self.query_one("#node-detail", NodeDetailWidget).set_node(node, path)
                self._update_context_hint(f"Selected: {node.content[:30]}... | 'b' branch, 'e' edit, 'g' grow")
        else:
            self.query_one("#node-detail", NodeDetailWidget).set_node(None)

    def _update_timeline(self) -> None:
        """Update the timeline widget with current tree history."""
        timeline = self.active_tree.get_timeline()
        self.query_one("#timeline", TimelineWidget).set_timeline(timeline)

    def _update_context_hint(self, hint: str) -> None:
        """Update the context hint at the bottom."""
        self.query_one("#context-hint", ContextInputWidget).set_hint(hint)

    async def action_new_seed(self) -> None:
        """Plant a new seed (root-level idea)."""
        content = await self.push_screen_wait(
            InputModal("Plant a Seed", "What's the idea?", "Press Enter to plant, Escape to cancel")
        )
        if content:
            context = await self.push_screen_wait(ContextModal("planting this seed"))
            node = self.active_tree.add_node(content, context=context)

            tree_widget = self.query_one("#idea-tree", IdeaTreeWidget)
            tree_widget.set_tree(self.active_tree)
            tree_widget.root.expand_all()
            self._update_timeline()
            self._update_context_hint(f"Planted: {content[:30]}...")

    async def action_branch(self) -> None:
        """Create a branch from the selected node."""
        tree_widget = self.query_one("#idea-tree", IdeaTreeWidget)
        selected = tree_widget.cursor_node

        if not selected or selected == tree_widget.root:
            self._update_context_hint("Select a node first to branch from it.")
            return

        content = await self.push_screen_wait(
            InputModal("Create Branch", "Branch into what?", "A new direction from this idea")
        )
        if content:
            context = await self.push_screen_wait(ContextModal("creating this branch"))
            tree_widget.add_child_to_selected(content)
            # Update the context of the new node
            timeline = self.active_tree.get_timeline()
            if timeline:
                latest_node = timeline[0][1]
                if latest_node.content == content and context:
                    latest_node.history[-1].context = context

            self._update_timeline()
            self._update_context_hint(f"Branched: {content[:30]}...")

    async def action_edit(self) -> None:
        """Edit the selected node."""
        tree_widget = self.query_one("#idea-tree", IdeaTreeWidget)
        selected = tree_widget.cursor_node

        if not selected or not selected.data:
            self._update_context_hint("Select a node to edit.")
            return

        node = self.active_tree.get_node(selected.data)
        if not node:
            return

        content = await self.push_screen_wait(
            InputModal("Edit Node", node.content)
        )
        if content and content != node.content:
            context = await self.push_screen_wait(ContextModal("making this edit"))
            node.edit(content, context)
            tree_widget.refresh_node(node.id)
            self._update_timeline()

            # Update detail view
            path = self.active_tree.get_path_to_root(node.id)
            self.query_one("#node-detail", NodeDetailWidget).set_node(node, path)
            self._update_context_hint(f"Edited: {content[:30]}...")

    async def _change_state(self, new_state: NodeState, action_verb: str) -> None:
        """Change the state of the selected node."""
        tree_widget = self.query_one("#idea-tree", IdeaTreeWidget)
        selected = tree_widget.cursor_node

        if not selected or not selected.data:
            self._update_context_hint(f"Select a node to {action_verb}.")
            return

        node = self.active_tree.get_node(selected.data)
        if not node:
            return

        context = await self.push_screen_wait(ContextModal(f"{action_verb}ing this idea"))
        node.set_state(new_state, context)
        tree_widget.refresh_node(node.id)
        self._update_timeline()

        path = self.active_tree.get_path_to_root(node.id)
        self.query_one("#node-detail", NodeDetailWidget).set_node(node, path)
        self._update_context_hint(f"Now {new_state.value}: {node.content[:30]}...")

    async def action_grow(self) -> None:
        """Mark a node as growing/mature."""
        tree_widget = self.query_one("#idea-tree", IdeaTreeWidget)
        selected = tree_widget.cursor_node
        if selected and selected.data:
            node = self.active_tree.get_node(selected.data)
            if node:
                # Cycle through growth states
                if node.state in (NodeState.SEED, NodeState.SPROUTING):
                    await self._change_state(NodeState.GROWING, "grow")
                elif node.state == NodeState.GROWING:
                    await self._change_state(NodeState.MATURE, "matur")
                else:
                    await self._change_state(NodeState.GROWING, "reviv")

    async def action_prune(self) -> None:
        """Mark a node as pruned."""
        await self._change_state(NodeState.PRUNED, "prun")

    async def action_dormant(self) -> None:
        """Mark a node as dormant."""
        await self._change_state(NodeState.DORMANT, "pause")

    def action_toggle_timeline(self) -> None:
        """Toggle timeline visibility."""
        try:
            timeline_container = self.query_one("#timeline-container")
            timeline_container.display = not timeline_container.display
        except NoMatches:
            pass

    def action_help(self) -> None:
        """Show help."""
        self._update_context_hint(
            "n:new seed | b:branch | e:edit | g:grow | p:prune | d:dormant | t:timeline | q:quit"
        )


def main():
    """Entry point for the application."""
    app = DendriteApp()
    app.run()


if __name__ == "__main__":
    main()
