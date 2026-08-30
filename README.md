# warroom

A terminal application for collaborative investigation — you and a set of AI witnesses working through a problem together. Built on Textual.

## What's here

- `warroom/app.py` — the Textual application and screens.
- `warroom/witnesses/` — the AI participants; `base.py` defines the interface a witness implements.
- `warroom/lenses/` — three ways of looking at the same investigation: `timeline.py` (chronological), `river.py` (flow), `constellation.py` (relational).
- `warroom/core/` — `models.py` for the domain types, `persistence.py` for the aiosqlite store.
- `warroom/ui/` — `theatre.py` and `widgets.py`, the presentation layer.

## Running it

```bash
pip install -e .
warroom
```

Requires Python 3.11+. Depends on Textual, Rich, Pydantic and aiosqlite.

## Status

Early — version 0.1.0, three commits. The structure is laid out and the lenses are the idea worth keeping.
