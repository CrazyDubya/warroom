"""
War Room - Collaborative Investigation Environment

A TUI for focused work with AI witnesses. The War Room is the center
from which all other views (lenses) emanate:

- CONSTELLATION: Spatial view of knowledge connections
- RIVER: Temporal view of knowledge, flowing into the past
- TIMELINE: Causal history of an artifact
- THEATRE: Deep focus mode for single artifacts

Core concepts:
- Focus: The atomic unit of investigation
- Witness: AI agents that observe and contribute
- Evidence: Pinned artifacts with attribution
- Hypothesis: Theories with confidence levels
"""

__version__ = "0.1.0"

from .app import WarRoomApp, demo, main

__all__ = ["WarRoomApp", "demo", "main"]
