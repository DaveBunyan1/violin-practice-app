"""
EVENT CONTRACTS

This module defines all data contracts used in the real-time pipeline.

Rules:
- Events are immutable once emitted
- Each event belongs to exactly one pipeline layer
- Downstream layers must not mutate upstream meaning
- Time domain must never be mixed within a single event type
  (perf_counter vs session-relative must not coexist in same field)
"""

from typing import Optional, TypedDict


# 1. Raw Data Ingestion Layer
class PitchObservationEvent(TypedDict):
    """Raw frequency data emitted from the Pitch Detection stage."""

    frequency: float
    note: str
    timestamp: float  # perf_counter absolute time
    pitch_cents_error: Optional[float]


# 2. Segmented Data Layer
class PerformedNoteEvent(TypedDict):
    """
    A stabilized note emitted by NoteSegmenter.
    All timestamps are in perf_counter time domain.
    """

    note: str
    frequency: float
    avg_pitch_error_cents: Optional[float]
    start_time: float
    end_time: float

    duration: float  # derived (end_time - start_time)


# 3. Session event
class SessionStoredNote(TypedDict):
    note: str
    frequency: float
    avg_pitch_error_cents: Optional[float]
    start_time: float  # Session-relative time (seconds from start)
    end_time: float  # Session-relative time (seconds from start)
    duration: float


# 4. Alignment Layer
class AlignedNote(TypedDict):
    """
    The result of mapping a performed note against the expected score entry.
    AlignedNote is a PURE DERIVED STRUCTURE.
    No computation should mutate source timing semantics.
    """

    expected_note: str
    performed_note: Optional[str]

    expected_time: float
    performed_start_time: Optional[float]
    performed_end_time: Optional[float]

    pitch_error_cents: Optional[float]
    time_error: Optional[float]

    match_quality: float


# 5. Scoring Layer
class ScoreResult(TypedDict):
    total_score: float
    pitch_accuracy: float
    timing_accuracy: float
    notes_hit: int
    notes_total: int


class LiveDashboardMetrics(TypedDict):
    """Payload containing real-time pitch tracking and target matching."""

    frequency: float
    note: str
    time: float

    expected_note: Optional[str]
    pitch_cents_error: Optional[float]


class WebSocketBroadcastEvent(TypedDict):
    """Top-level framing wrapper for WebSocket frame transport."""

    type: str  # e.g., "pitch"
    data: LiveDashboardMetrics
