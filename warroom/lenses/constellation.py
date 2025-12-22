"""
Constellation Lens - Spatial view of knowledge.

Shows focuses, evidence, and their relationships as a
force-directed graph rendered in character space.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional

from rich.console import RenderableType
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from warroom.core import Evidence, Focus, WarRoomState


@dataclass
class Node:
    """A node in the constellation."""
    id: str
    label: str
    x: float = 0.0
    y: float = 0.0
    node_type: str = "focus"  # focus, evidence, tag
    weight: float = 1.0
    is_current: bool = False

    # For physics simulation
    vx: float = 0.0
    vy: float = 0.0


@dataclass
class Edge:
    """An edge between nodes."""
    source: str
    target: str
    weight: float = 1.0
    edge_type: str = "related"  # related, evidence, tag


@dataclass
class ConstellationGraph:
    """The graph structure for the constellation."""
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    width: int = 60
    height: int = 20

    def add_node(self, node: Node) -> None:
        """Add a node with random initial position."""
        if node.id not in self.nodes:
            node.x = random.uniform(5, self.width - 5)
            node.y = random.uniform(2, self.height - 2)
            self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        """Add an edge between nodes."""
        if edge.source in self.nodes and edge.target in self.nodes:
            self.edges.append(edge)

    def simulate_step(self, iterations: int = 50) -> None:
        """Run force-directed layout simulation."""
        k = math.sqrt((self.width * self.height) / max(len(self.nodes), 1))

        for _ in range(iterations):
            # Repulsion between all nodes
            for n1 in self.nodes.values():
                n1.vx = 0
                n1.vy = 0
                for n2 in self.nodes.values():
                    if n1.id != n2.id:
                        dx = n1.x - n2.x
                        dy = n1.y - n2.y
                        dist = max(math.sqrt(dx * dx + dy * dy), 0.1)
                        force = k * k / dist
                        n1.vx += (dx / dist) * force * 0.1
                        n1.vy += (dy / dist) * force * 0.1

            # Attraction along edges
            for edge in self.edges:
                n1 = self.nodes[edge.source]
                n2 = self.nodes[edge.target]
                dx = n2.x - n1.x
                dy = n2.y - n1.y
                dist = max(math.sqrt(dx * dx + dy * dy), 0.1)
                force = dist * dist / k * edge.weight
                n1.vx += (dx / dist) * force * 0.05
                n1.vy += (dy / dist) * force * 0.05
                n2.vx -= (dx / dist) * force * 0.05
                n2.vy -= (dy / dist) * force * 0.05

            # Apply velocities with bounds
            for node in self.nodes.values():
                node.x = max(3, min(self.width - 3, node.x + node.vx))
                node.y = max(1, min(self.height - 1, node.y + node.vy))

    def render_to_grid(self) -> list[list[str]]:
        """Render the graph to a character grid."""
        grid = [[" " for _ in range(self.width)] for _ in range(self.height)]

        # Draw edges first
        for edge in self.edges:
            n1 = self.nodes[edge.source]
            n2 = self.nodes[edge.target]
            self._draw_edge(grid, n1, n2, edge)

        # Draw nodes on top
        for node in self.nodes.values():
            self._draw_node(grid, node)

        return grid

    def _draw_edge(
        self, grid: list[list[str]], n1: Node, n2: Node, edge: Edge
    ) -> None:
        """Draw an edge between two nodes using Bresenham's line algorithm."""
        x1, y1 = int(n1.x), int(n1.y)
        x2, y2 = int(n2.x), int(n2.y)

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        # Edge character based on weight
        char = "━" if edge.weight > 0.7 else "─" if edge.weight > 0.3 else "╌"

        while True:
            if 0 <= y1 < len(grid) and 0 <= x1 < len(grid[0]):
                if grid[y1][x1] == " ":
                    grid[y1][x1] = char

            if x1 == x2 and y1 == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def _draw_node(self, grid: list[list[str]], node: Node) -> None:
        """Draw a node at its position."""
        x, y = int(node.x), int(node.y)

        if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
            if node.is_current:
                char = "◉"
            elif node.node_type == "focus":
                char = "●"
            elif node.node_type == "evidence":
                char = "◦"
            else:
                char = "○"

            grid[y][x] = char

            # Draw label (truncated)
            label = node.label[:8]
            start_x = max(0, x - len(label) // 2)
            label_y = y + 1 if y < len(grid) - 1 else y - 1

            if 0 <= label_y < len(grid):
                for i, c in enumerate(label):
                    lx = start_x + i
                    if 0 <= lx < len(grid[0]):
                        grid[label_y][lx] = c


class ConstellationView(Static):
    """The constellation view widget."""

    DEFAULT_CSS = """
    ConstellationView {
        height: 100%;
        padding: 1;
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
        self.graph = self._build_graph()

    def _build_graph(self) -> ConstellationGraph:
        """Build the constellation graph from state."""
        graph = ConstellationGraph(width=70, height=18)

        # Add focus nodes
        for focus in self.state.focuses:
            is_current = (
                self.current_focus and focus.id == self.current_focus.id
            )
            graph.add_node(Node(
                id=f"f:{focus.id}",
                label=focus.name[:10],
                node_type="focus",
                weight=len(focus.evidence) + len(focus.sessions),
                is_current=is_current,
            ))

        # Add evidence nodes for current focus
        if self.current_focus:
            for evidence in self.current_focus.evidence[:5]:
                graph.add_node(Node(
                    id=f"e:{evidence.id}",
                    label=evidence.title[:8],
                    node_type="evidence",
                    weight=evidence.relevance,
                ))
                graph.add_edge(Edge(
                    source=f"f:{self.current_focus.id}",
                    target=f"e:{evidence.id}",
                    weight=evidence.relevance,
                    edge_type="evidence",
                ))

        # Add edges between related focuses
        for focus in self.state.focuses:
            for related_id in focus.related:
                if self.state.get_focus(related_id):
                    graph.add_edge(Edge(
                        source=f"f:{focus.id}",
                        target=f"f:{related_id}",
                        weight=0.5,
                        edge_type="related",
                    ))

            # Connect by shared tags
            for other in self.state.focuses:
                if focus.id != other.id:
                    shared_tags = set(focus.tags) & set(other.tags)
                    if shared_tags:
                        graph.add_edge(Edge(
                            source=f"f:{focus.id}",
                            target=f"f:{other.id}",
                            weight=len(shared_tags) * 0.2,
                            edge_type="tag",
                        ))

        # Run simulation
        graph.simulate_step(iterations=100)

        return graph

    def render(self) -> RenderableType:
        grid = self.graph.render_to_grid()

        text = Text()
        text.append("WAR ROOM > CONSTELLATION LENS", style="bold cyan")
        text.append("                    [ESC to return]\n", style="dim")
        text.append("─" * 70 + "\n", style="dim")

        for row in grid:
            line = "".join(row)
            # Colorize nodes
            line = line.replace("◉", "[bold cyan]◉[/]")
            line = line.replace("●", "[yellow]●[/]")
            line = line.replace("◦", "[dim]◦[/]")
            text.append(line + "\n")

        text.append("─" * 70 + "\n", style="dim")
        text.append(
            "[hjkl] navigate  [enter] focus  [/] search  ",
            style="dim",
        )

        return text


class ConstellationLens:
    """The Constellation lens - spatial view of knowledge."""

    name = "constellation"
    description = "Spatial relationships between focuses and evidence"

    def __init__(self, state: WarRoomState):
        self.state = state

    def create_view(self, current_focus: Optional[Focus] = None) -> Widget:
        """Create the constellation view widget."""
        return ConstellationView(self.state, current_focus)
