"""
Persistence layer for the War Room.

Saves and loads state to/from JSON files. Future versions
could use SQLite for more complex queries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import WarRoomState


DEFAULT_STATE_PATH = Path.home() / ".warroom" / "state.json"


class StateManager:
    """Manages persistence of War Room state."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or DEFAULT_STATE_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, state: WarRoomState) -> None:
        """Save state to disk."""
        with open(self.path, "w") as f:
            f.write(state.model_dump_json(indent=2))

    def load(self) -> WarRoomState:
        """Load state from disk, or create new if none exists."""
        if not self.path.exists():
            return WarRoomState()

        try:
            with open(self.path) as f:
                data = json.load(f)
            return WarRoomState.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            # Corrupted state, start fresh
            return WarRoomState()

    def exists(self) -> bool:
        """Check if state file exists."""
        return self.path.exists()
