"""
Core data models for the War Room.

The fundamental units:
- Focus: The atomic unit of investigation
- Evidence: Pinned artifacts with attribution
- Hypothesis: A theory with confidence
- Session: A period of work on a focus
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FocusHealth(str, Enum):
    """The health state of a focus - like a plant in a garden."""
    NASCENT = "nascent"      # 🌱 Just started
    GROWING = "growing"      # 🌿 Active progress
    BLOOMING = "blooming"    # 🌸 Peak engagement
    STALLED = "stalled"      # 🥀 No activity
    DORMANT = "dormant"      # 💤 Intentionally paused
    RESOLVED = "resolved"    # ✓ Completed


class WitnessType(str, Enum):
    """The personality/specialty of an AI witness."""
    CRITIC = "critic"           # Challenges assumptions, finds flaws
    HISTORIAN = "historian"     # Searches past, finds patterns
    ARCHITECT = "architect"     # Designs solutions, sees structure
    SHERLOCK = "sherlock"       # Investigates, forms hypotheses
    GARDENER = "gardener"       # Tracks health, suggests priorities
    SCRIBE = "scribe"           # Summarizes, documents


class EvidenceSource(str, Enum):
    """Where evidence came from."""
    USER = "user"               # Human pinned it
    WITNESS = "witness"         # An agent found it
    MEMORY = "memory"           # Surfaced from MEMEX
    EXTERNAL = "external"       # From outside (file, url, etc)


class Evidence(BaseModel):
    """
    Something pinned to a focus.

    Evidence is the shared artifact that witnesses and humans
    collaborate around. It has provenance and decays over time
    if not referenced.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    content: str
    source: EvidenceSource
    source_detail: Optional[str] = None  # e.g., witness name, file path
    pinned_at: datetime = Field(default_factory=datetime.now)
    last_referenced: datetime = Field(default_factory=datetime.now)
    relevance: float = 1.0  # Decays over time if not referenced
    tags: list[str] = Field(default_factory=list)

    def reference(self) -> None:
        """Mark this evidence as referenced, boosting relevance."""
        self.last_referenced = datetime.now()
        self.relevance = min(1.0, self.relevance + 0.1)

    def decay(self, factor: float = 0.95) -> None:
        """Apply time decay to relevance."""
        self.relevance *= factor


class Hypothesis(BaseModel):
    """
    A theory proposed by a witness.

    Hypotheses have confidence levels and can be confirmed,
    rejected, or refined.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    witness: WitnessType
    statement: str
    confidence: float = 0.5  # 0.0 to 1.0
    supporting_evidence: list[str] = Field(default_factory=list)  # Evidence IDs
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "active"  # active, confirmed, rejected, refined


class Session(BaseModel):
    """
    A period of work on a focus.

    Sessions track engagement over time, feeding into
    the Garden view of project health.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    duration_minutes: int = 0
    notes: str = ""
    evidence_added: list[str] = Field(default_factory=list)
    hypotheses_generated: list[str] = Field(default_factory=list)


class Focus(BaseModel):
    """
    The atomic unit of investigation.

    A Focus is what you're working on. It has witnesses (AI agents),
    evidence (shared artifacts), hypotheses (theories), and sessions
    (periods of work).

    The Focus is the center of the War Room.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    question: Optional[str] = None  # The driving question
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    health: FocusHealth = FocusHealth.NASCENT

    # The witnesses observing this focus
    witnesses: list[WitnessType] = Field(default_factory=lambda: [
        WitnessType.CRITIC,
        WitnessType.HISTORIAN,
    ])

    # Evidence board
    evidence: list[Evidence] = Field(default_factory=list)

    # Hypotheses from witnesses
    hypotheses: list[Hypothesis] = Field(default_factory=list)

    # Work sessions
    sessions: list[Session] = Field(default_factory=list)

    # Related focuses
    related: list[str] = Field(default_factory=list)  # Focus IDs

    # Tags for constellation navigation
    tags: list[str] = Field(default_factory=list)

    def add_evidence(
        self,
        title: str,
        content: str,
        source: EvidenceSource,
        source_detail: Optional[str] = None,
    ) -> Evidence:
        """Add evidence to the board."""
        evidence = Evidence(
            title=title,
            content=content,
            source=source,
            source_detail=source_detail,
        )
        self.evidence.append(evidence)
        self.updated_at = datetime.now()
        return evidence

    def add_hypothesis(
        self,
        witness: WitnessType,
        statement: str,
        confidence: float = 0.5,
        supporting_evidence: Optional[list[str]] = None,
    ) -> Hypothesis:
        """Add a hypothesis from a witness."""
        hypothesis = Hypothesis(
            witness=witness,
            statement=statement,
            confidence=confidence,
            supporting_evidence=supporting_evidence or [],
        )
        self.hypotheses.append(hypothesis)
        self.updated_at = datetime.now()
        return hypothesis

    def start_session(self) -> Session:
        """Start a new work session."""
        session = Session()
        self.sessions.append(session)
        self.health = FocusHealth.GROWING
        self.updated_at = datetime.now()
        return session

    def end_session(self, session: Session, notes: str = "") -> None:
        """End a work session."""
        session.ended_at = datetime.now()
        session.duration_minutes = int(
            (session.ended_at - session.started_at).total_seconds() / 60
        )
        session.notes = notes

    def calculate_health(self) -> FocusHealth:
        """Calculate health based on activity patterns."""
        if not self.sessions:
            return FocusHealth.NASCENT

        last_session = max(self.sessions, key=lambda s: s.started_at)
        days_since = (datetime.now() - last_session.started_at).days

        if days_since > 14:
            return FocusHealth.DORMANT
        elif days_since > 7:
            return FocusHealth.STALLED

        # Check recent activity intensity
        recent_sessions = [
            s for s in self.sessions
            if (datetime.now() - s.started_at).days < 7
        ]

        if len(recent_sessions) >= 5:
            return FocusHealth.BLOOMING
        elif len(recent_sessions) >= 2:
            return FocusHealth.GROWING
        else:
            return FocusHealth.NASCENT

    @property
    def active_hypotheses(self) -> list[Hypothesis]:
        """Get hypotheses that are still active."""
        return [h for h in self.hypotheses if h.status == "active"]

    @property
    def high_confidence_hypotheses(self) -> list[Hypothesis]:
        """Get hypotheses with high confidence."""
        return [h for h in self.active_hypotheses if h.confidence >= 0.7]


class WarRoomState(BaseModel):
    """
    The overall state of the War Room.

    Contains all focuses and provides navigation between them.
    """
    focuses: list[Focus] = Field(default_factory=list)
    active_focus_id: Optional[str] = None

    def get_focus(self, focus_id: str) -> Optional[Focus]:
        """Get a focus by ID."""
        for focus in self.focuses:
            if focus.id == focus_id:
                return focus
        return None

    @property
    def active_focus(self) -> Optional[Focus]:
        """Get the currently active focus."""
        if self.active_focus_id:
            return self.get_focus(self.active_focus_id)
        return None

    def create_focus(self, name: str, question: Optional[str] = None) -> Focus:
        """Create a new focus."""
        focus = Focus(name=name, question=question)
        self.focuses.append(focus)
        self.active_focus_id = focus.id
        return focus

    def get_focuses_by_health(self, health: FocusHealth) -> list[Focus]:
        """Get all focuses with a specific health state."""
        return [f for f in self.focuses if f.calculate_health() == health]

    def get_stalled_focuses(self) -> list[Focus]:
        """Get focuses that need attention."""
        return [
            f for f in self.focuses
            if f.calculate_health() in (FocusHealth.STALLED, FocusHealth.DORMANT)
        ]
