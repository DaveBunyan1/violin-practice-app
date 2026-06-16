from typing import Optional, TypedDict


# 1. Raw Data Ingestion Layer
class PitchObservationEvent(TypedDict):
    """Raw frequency data emitted from the Pitch Detection stage."""

    frequency: float
    note: str
    timestamp: float


# 2. Segmented Data Layer
class PerformedNoteEvent(TypedDict):
    """A stabilized, segmented note event emitted by NoteSegmenter."""

    note: str
    frequency: float
    timestamp: float  # onset time


class LiveDashboardMetrics(TypedDict):
    """Payload containing real-time pitch tracking and target matching."""

    frequency: float
    note: str
    time: float
    expected_note: Optional[str]


class WebSocketBroadcastEvent(TypedDict):
    """Top-level framing wrapper for WebSocket frame transport."""

    type: str  # e.g., "pitch"
    data: LiveDashboardMetrics


# 4. Alignment Layer
class AlignedNote(TypedDict):
    """The result of mapping a performed note against the expected score entry."""

    expected_note: str
    performed_note: Optional[str]

    expected_time: float
    performed_time: Optional[float]

    pitch_error_cents: Optional[float]
    time_error: Optional[float]

    match_quality: float
