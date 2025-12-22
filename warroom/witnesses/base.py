"""
Witness system - AI agents that observe and contribute.

Each witness has a personality and specialty. They observe the focus,
generate hypotheses, find evidence, and offer whispers (suggestions).

In a real implementation, these would call an LLM. For the PE,
they simulate behavior with templates and heuristics.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from warroom.core.models import (
    Evidence,
    EvidenceSource,
    Focus,
    Hypothesis,
    WitnessType,
)


@dataclass
class Whisper:
    """
    A suggestion from a witness.

    Whispers are low-priority, ambient suggestions that don't
    demand attention. They can be ignored without consequence.
    """
    witness: WitnessType
    message: str
    priority: float = 0.5  # 0.0 to 1.0
    action: Optional[str] = None  # Optional action the user can take
    evidence_id: Optional[str] = None  # Related evidence if any


@dataclass
class Observation:
    """
    An observation a witness makes about the current state.

    Observations can lead to hypotheses or whispers.
    """
    witness: WitnessType
    insight: str
    confidence: float = 0.5


class Witness(ABC):
    """
    Base class for all witnesses.

    Witnesses observe focuses and contribute insights.
    """

    witness_type: WitnessType
    name: str
    description: str

    @abstractmethod
    def observe(self, focus: Focus) -> list[Observation]:
        """Observe the current focus and generate observations."""
        pass

    @abstractmethod
    def generate_whisper(self, focus: Focus) -> Optional[Whisper]:
        """Generate a whisper based on the current state."""
        pass

    @abstractmethod
    def generate_hypothesis(
        self, focus: Focus, observation: Observation
    ) -> Optional[Hypothesis]:
        """Generate a hypothesis from an observation."""
        pass

    def get_personality_prefix(self) -> str:
        """Get the personality-appropriate prefix for messages."""
        return f"{self.name}:"


class CriticWitness(Witness):
    """
    The Critic challenges assumptions and finds flaws.

    Asks uncomfortable questions. Points out contradictions.
    Never satisfied with the first answer.
    """

    witness_type = WitnessType.CRITIC
    name = "CRITIC"
    description = "Challenges assumptions, finds flaws"

    CHALLENGES = [
        "Have you considered the opposite might be true?",
        "This contradicts what you noted earlier.",
        "What's the strongest argument against this?",
        "You're assuming {assumption}. Is that valid?",
        "This solution feels too simple. What are you missing?",
        "Everyone else does it differently. Why are you right?",
    ]

    def observe(self, focus: Focus) -> list[Observation]:
        observations = []

        # Look for contradictions in evidence
        if len(focus.evidence) >= 2:
            observations.append(Observation(
                witness=self.witness_type,
                insight="Multiple evidence items may have conflicting implications",
                confidence=0.4,
            ))

        # Challenge high-confidence hypotheses
        for hyp in focus.high_confidence_hypotheses:
            observations.append(Observation(
                witness=self.witness_type,
                insight=f"High confidence on '{hyp.statement[:50]}...' - but is it tested?",
                confidence=0.6,
            ))

        return observations

    def generate_whisper(self, focus: Focus) -> Optional[Whisper]:
        if not focus.evidence and not focus.hypotheses:
            return Whisper(
                witness=self.witness_type,
                message="No evidence yet. Are you investigating or assuming?",
                priority=0.3,
            )

        if focus.high_confidence_hypotheses:
            hyp = random.choice(focus.high_confidence_hypotheses)
            return Whisper(
                witness=self.witness_type,
                message=f'"{hyp.statement[:40]}..." - what would prove this wrong?',
                priority=0.6,
            )

        return Whisper(
            witness=self.witness_type,
            message=random.choice(self.CHALLENGES),
            priority=0.4,
        )

    def generate_hypothesis(
        self, focus: Focus, observation: Observation
    ) -> Optional[Hypothesis]:
        # Critic rarely generates hypotheses - mostly challenges them
        return None


class HistorianWitness(Witness):
    """
    The Historian searches the past and finds patterns.

    Remembers what you've done before. Finds similar situations.
    Surfaces forgotten knowledge.
    """

    witness_type = WitnessType.HISTORIAN
    name = "HISTORIAN"
    description = "Searches past, finds patterns"

    PATTERNS = [
        "You've encountered something similar before...",
        "In {project}, you solved this differently.",
        "This pattern appeared in your notes from {time}.",
        "The last time you tried this approach, {outcome}.",
        "Your past self had thoughts on this.",
    ]

    def observe(self, focus: Focus) -> list[Observation]:
        observations = []

        # Simulate finding patterns
        if focus.tags:
            observations.append(Observation(
                witness=self.witness_type,
                insight=f"Tags {focus.tags} appear in previous work",
                confidence=0.5,
            ))

        # Check for long-running focuses
        if focus.sessions and len(focus.sessions) > 3:
            observations.append(Observation(
                witness=self.witness_type,
                insight="This focus has been active across many sessions",
                confidence=0.7,
            ))

        return observations

    def generate_whisper(self, focus: Focus) -> Optional[Whisper]:
        if not focus.sessions:
            return Whisper(
                witness=self.witness_type,
                message="First session on this topic. Let me search your history...",
                priority=0.3,
            )

        templates = [
            f"You've worked on '{focus.name}' for {len(focus.sessions)} sessions.",
            "Similar work in your history might be relevant.",
            "Your notes from past projects could help here.",
        ]

        return Whisper(
            witness=self.witness_type,
            message=random.choice(templates),
            priority=0.4,
        )

    def generate_hypothesis(
        self, focus: Focus, observation: Observation
    ) -> Optional[Hypothesis]:
        if "pattern" in observation.insight.lower():
            return Hypothesis(
                witness=self.witness_type,
                statement="Historical patterns suggest a similar solution may apply",
                confidence=0.4,
            )
        return None


class ArchitectWitness(Witness):
    """
    The Architect designs solutions and sees structure.

    Thinks in systems. Proposes designs. Sees the big picture.
    """

    witness_type = WitnessType.ARCHITECT
    name = "ARCHITECT"
    description = "Designs solutions, sees structure"

    def observe(self, focus: Focus) -> list[Observation]:
        observations = []

        # Look for structural patterns in evidence
        if len(focus.evidence) > 3:
            observations.append(Observation(
                witness=self.witness_type,
                insight="Evidence suggests a structural pattern emerging",
                confidence=0.5,
            ))

        # Check for related focuses
        if focus.related:
            observations.append(Observation(
                witness=self.witness_type,
                insight=f"This focus connects to {len(focus.related)} others",
                confidence=0.6,
            ))

        return observations

    def generate_whisper(self, focus: Focus) -> Optional[Whisper]:
        templates = [
            "Consider the overall structure here.",
            "What's the relationship between the components?",
            "A diagram might clarify the dependencies.",
            "Think about this at a higher level of abstraction.",
        ]

        return Whisper(
            witness=self.witness_type,
            message=random.choice(templates),
            priority=0.4,
        )

    def generate_hypothesis(
        self, focus: Focus, observation: Observation
    ) -> Optional[Hypothesis]:
        if "structural" in observation.insight.lower():
            return Hypothesis(
                witness=self.witness_type,
                statement="The evidence points to a modular design approach",
                confidence=0.5,
            )
        return None


class SherlockWitness(Witness):
    """
    Sherlock investigates and forms hypotheses.

    The detective. Follows clues. Builds theories.
    High confidence when evidence aligns.
    """

    witness_type = WitnessType.SHERLOCK
    name = "SHERLOCK"
    description = "Investigates, forms hypotheses"

    def observe(self, focus: Focus) -> list[Observation]:
        observations = []

        # Analyze evidence for patterns
        if focus.evidence:
            observations.append(Observation(
                witness=self.witness_type,
                insight=f"Analyzing {len(focus.evidence)} pieces of evidence...",
                confidence=0.6,
            ))

        # Look for gaps
        if focus.question and not focus.hypotheses:
            observations.append(Observation(
                witness=self.witness_type,
                insight="Question posed but no hypotheses formed yet",
                confidence=0.4,
            ))

        return observations

    def generate_whisper(self, focus: Focus) -> Optional[Whisper]:
        if not focus.evidence:
            return Whisper(
                witness=self.witness_type,
                message="We need evidence to investigate. What do we know?",
                priority=0.5,
            )

        if focus.evidence and not focus.hypotheses:
            return Whisper(
                witness=self.witness_type,
                message="I see evidence but no theory. Let me form a hypothesis...",
                priority=0.6,
                action="generate_hypothesis",
            )

        return Whisper(
            witness=self.witness_type,
            message="Following the trail of evidence...",
            priority=0.3,
        )

    def generate_hypothesis(
        self, focus: Focus, observation: Observation
    ) -> Optional[Hypothesis]:
        if focus.evidence:
            # Base confidence on evidence count
            confidence = min(0.9, 0.3 + (len(focus.evidence) * 0.1))
            evidence_ids = [e.id for e in focus.evidence[:3]]

            return Hypothesis(
                witness=self.witness_type,
                statement=f"Based on {len(focus.evidence)} evidence items, a pattern emerges",
                confidence=confidence,
                supporting_evidence=evidence_ids,
            )
        return None


class GardenerWitness(Witness):
    """
    The Gardener tracks health and suggests priorities.

    Looks at the big picture across focuses. Knows what's
    being neglected. Suggests what to tend to.
    """

    witness_type = WitnessType.GARDENER
    name = "GARDENER"
    description = "Tracks health, suggests priorities"

    def observe(self, focus: Focus) -> list[Observation]:
        observations = []

        health = focus.calculate_health()
        observations.append(Observation(
            witness=self.witness_type,
            insight=f"Focus health: {health.value}",
            confidence=0.9,
        ))

        return observations

    def generate_whisper(self, focus: Focus) -> Optional[Whisper]:
        health = focus.calculate_health()

        messages = {
            "nascent": "This focus is young. It needs consistent attention to grow.",
            "growing": "Good progress. Keep the momentum.",
            "blooming": "Peak engagement! Capture insights while they're fresh.",
            "stalled": "This focus needs attention. It's been quiet too long.",
            "dormant": "Should this be revisited or intentionally closed?",
            "resolved": "This focus is complete. Time to harvest the learnings.",
        }

        return Whisper(
            witness=self.witness_type,
            message=messages.get(health.value, "Observing growth patterns..."),
            priority=0.5 if health.value in ("stalled", "dormant") else 0.3,
        )

    def generate_hypothesis(
        self, focus: Focus, observation: Observation
    ) -> Optional[Hypothesis]:
        # Gardener doesn't generate hypotheses about the focus content
        return None


class WitnessPanel:
    """
    Manages a collection of witnesses for a focus.

    Coordinates observations, whispers, and hypotheses.
    """

    WITNESS_CLASSES = {
        WitnessType.CRITIC: CriticWitness,
        WitnessType.HISTORIAN: HistorianWitness,
        WitnessType.ARCHITECT: ArchitectWitness,
        WitnessType.SHERLOCK: SherlockWitness,
        WitnessType.GARDENER: GardenerWitness,
    }

    def __init__(self, focus: Focus):
        self.focus = focus
        self.witnesses: dict[WitnessType, Witness] = {}

        for wtype in focus.witnesses:
            if wtype in self.WITNESS_CLASSES:
                self.witnesses[wtype] = self.WITNESS_CLASSES[wtype]()

    def get_all_observations(self) -> list[Observation]:
        """Get observations from all witnesses."""
        observations = []
        for witness in self.witnesses.values():
            observations.extend(witness.observe(self.focus))
        return observations

    def get_whispers(self, limit: int = 3) -> list[Whisper]:
        """Get whispers from all witnesses, sorted by priority."""
        whispers = []
        for witness in self.witnesses.values():
            whisper = witness.generate_whisper(self.focus)
            if whisper:
                whispers.append(whisper)

        # Sort by priority, take top N
        whispers.sort(key=lambda w: w.priority, reverse=True)
        return whispers[:limit]

    def generate_hypotheses(self) -> list[Hypothesis]:
        """Generate hypotheses from observations."""
        hypotheses = []
        observations = self.get_all_observations()

        for obs in observations:
            witness = self.witnesses.get(obs.witness)
            if witness:
                hyp = witness.generate_hypothesis(self.focus, obs)
                if hyp:
                    hypotheses.append(hyp)

        return hypotheses

    def add_witness(self, witness_type: WitnessType) -> None:
        """Add a witness to the panel."""
        if witness_type in self.WITNESS_CLASSES:
            self.witnesses[witness_type] = self.WITNESS_CLASSES[witness_type]()
            if witness_type not in self.focus.witnesses:
                self.focus.witnesses.append(witness_type)

    def remove_witness(self, witness_type: WitnessType) -> None:
        """Remove a witness from the panel."""
        if witness_type in self.witnesses:
            del self.witnesses[witness_type]
            if witness_type in self.focus.witnesses:
                self.focus.witnesses.remove(witness_type)
