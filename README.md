# warroom

A Textual terminal application described in its own docstring as "a collaborative investigation environment where you and AI witnesses work together to explore, debug, design, and understand."

## What's here

- `warroom/app.py` — the Textual application and screens.
- `warroom/witnesses/` — the AI participants; `base.py` defines the interface.
- `warroom/lenses/` — three views over the same material, per their module docstrings:
  - `river.py` — temporal. Knowledge by time, recent items crisp and older ones compressed and faded.
  - `constellation.py` — spatial. Focuses, evidence and their relationships as a force-directed graph rendered in character space.
  - `timeline.py` — causal. The biography of a single focus: how it came to be and what influenced it.
- `warroom/core/` — `models.py` for domain types, `persistence.py` for the aiosqlite store.
- `warroom/ui/` — `theatre.py` and `widgets.py`.

## Running it

```bash
pip install -e .
warroom
```

Python 3.11+. Depends on Textual, Rich, Pydantic and aiosqlite.

## Status

Version 0.1.0, three commits.
