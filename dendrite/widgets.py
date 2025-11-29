"""Custom widgets for Dendrite TUI."""
from __future__ import annotations

from rich.text import Text
from textual.widgets import Static, Tree as TextualTree
from textual.widgets.tree import TreeNode

from .models import Node, Tree, NodeState


class IdeaTreeWidget(TextualTree):
    """A visual tree of ideas with state indicators."""

    def __init__(self, tree: Tree | None = None, **kwargs):
        super().__init__("Ideas", **kwargs)
        self.idea_tree = tree
        self._node_map: dict[str, TreeNode] = {}

    def set_tree(self, tree: Tree) -> None:
        """Set or replace the tree being displayed."""
        self.idea_tree = tree
        self.clear()
        self.root.label = tree.name
        self._node_map.clear()

        # Build the visual tree from roots
        for root_id in tree.root_ids:
            root_node = tree.get_node(root_id)
            if root_node:
                self._add_node_recursive(root_node, self.root)

        self.root.expand()

    def _add_node_recursive(self, node: Node, parent: TreeNode) -> None:
        """Recursively add nodes to the visual tree."""
        label = self._format_node_label(node)
        tree_node = parent.add(label, data=node.id)
        self._node_map[node.id] = tree_node

        if self.idea_tree:
            for child in self.idea_tree.get_children(node.id):
                self._add_node_recursive(child, tree_node)

    def _format_node_label(self, node: Node) -> Text:
        """Format a node's label with icon and styling."""
        text = Text()

        # State icon
        text.append(f"{node.state_icon} ", style="bold")

        # Content (truncated if long)
        content = node.content[:40] + "..." if len(node.content) > 40 else node.content

        # Style based on state
        style_map = {
            NodeState.SEED: "italic dim",
            NodeState.SPROUTING: "italic",
            NodeState.GROWING: "",
            NodeState.MATURE: "bold",
            NodeState.DORMANT: "dim",
            NodeState.PRUNED: "strike dim",
        }
        text.append(content, style=style_map.get(node.state, ""))

        # Age indicator
        text.append(f" ({node.age_display})", style="dim")

        return text

    def refresh_node(self, node_id: str) -> None:
        """Refresh the display of a specific node."""
        if node_id in self._node_map and self.idea_tree:
            node = self.idea_tree.get_node(node_id)
            if node:
                self._node_map[node_id].label = self._format_node_label(node)

    def add_child_to_selected(self, content: str) -> str | None:
        """Add a child node to the currently selected node."""
        if not self.idea_tree:
            return None

        selected = self.cursor_node
        if selected and selected.data:
            parent_id = selected.data
            new_node = self.idea_tree.branch(parent_id, content)
            label = self._format_node_label(new_node)
            new_tree_node = selected.add(label, data=new_node.id)
            self._node_map[new_node.id] = new_tree_node
            selected.expand()
            return new_node.id
        elif selected == self.root:
            # Adding to root
            new_node = self.idea_tree.add_node(content)
            label = self._format_node_label(new_node)
            new_tree_node = self.root.add(label, data=new_node.id)
            self._node_map[new_node.id] = new_tree_node
            return new_node.id
        return None


class TimelineWidget(Static):
    """A widget showing the temporal history of changes."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timeline_data: list = []

    def set_timeline(self, timeline: list) -> None:
        """Set the timeline data to display."""
        self.timeline_data = timeline
        self._render_timeline()

    def _render_timeline(self) -> None:
        """Render the timeline as rich text."""
        if not self.timeline_data:
            self.update("No history yet...")
            return

        text = Text()
        text.append("━━━ Timeline ━━━\n\n", style="bold cyan")

        for i, (timestamp, node, moment) in enumerate(self.timeline_data[:15]):
            # Time marker
            time_str = timestamp.strftime("%H:%M")
            date_str = timestamp.strftime("%m/%d")
            text.append(f"  {date_str} ", style="dim")
            text.append(f"{time_str}", style="cyan")

            # Action
            action_styles = {
                "created": "green",
                "edited": "yellow",
                "state:mature": "bold green",
                "state:pruned": "red",
                "state:dormant": "dim",
            }
            action_style = action_styles.get(moment.action, "white")
            text.append(f"  {moment.action:<12}", style=action_style)

            # Content preview
            preview = moment.content_snapshot[:30] + "..." if len(moment.content_snapshot) > 30 else moment.content_snapshot
            text.append(f"  {preview}\n", style="white")

            # Context if present
            if moment.context:
                text.append(f"            └─ {moment.context}\n", style="dim italic")

        self.update(text)


class NodeDetailWidget(Static):
    """Shows detailed information about a selected node."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_node: Node | None = None

    def set_node(self, node: Node | None, path: list[Node] | None = None) -> None:
        """Display details for a node."""
        self.current_node = node
        if not node:
            self.update("Select a node to see details...")
            return

        text = Text()

        # Header with state
        text.append(f"\n  {node.state_icon} ", style="bold")
        text.append(f"{node.state.value.upper()}\n", style="bold cyan")

        # Content
        text.append("\n  ─── Content ───\n", style="dim")
        text.append(f"  {node.content}\n", style="white")

        # Path to root (breadcrumb)
        if path and len(path) > 1:
            text.append("\n  ─── Path ───\n", style="dim")
            breadcrumb = " → ".join([n.content[:15] + "..." if len(n.content) > 15 else n.content for n in reversed(path)])
            text.append(f"  {breadcrumb}\n", style="italic")

        # Metadata
        text.append("\n  ─── Info ───\n", style="dim")
        text.append(f"  ID: ", style="dim")
        text.append(f"{node.id}\n", style="cyan")
        text.append(f"  Created: ", style="dim")
        text.append(f"{node.age_display}\n", style="white")
        text.append(f"  Changes: ", style="dim")
        text.append(f"{len(node.history)}\n", style="white")

        # History preview
        if node.history:
            text.append("\n  ─── Recent ───\n", style="dim")
            for moment in node.history[-3:]:
                time_str = moment.timestamp.strftime("%H:%M")
                text.append(f"  {time_str} ", style="cyan")
                text.append(f"{moment.action}\n", style="yellow")

        self.update(text)


class ContextInputWidget(Static):
    """Widget for showing contextual prompts and hints."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_hint("Welcome to Dendrite. Press 'n' to plant a new seed.")

    def set_hint(self, hint: str) -> None:
        """Set the contextual hint."""
        text = Text()
        text.append(" 💡 ", style="yellow")
        text.append(hint, style="italic")
        self.update(text)
