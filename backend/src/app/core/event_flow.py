from enum import Enum


class EventSource(str, Enum):
    AUDIO = "audio"
    SEGMENTER = "segmenter"
    SESSION = "session"
    ALIGNMENT = "alignment"
    SCORING = "scoring"


def validate_event_flow(event_type: str, source: EventSource) -> None:
    """
    Enforces event ownership rules at runtime (debug mode only).
    """

    rules = {
        "PitchObservationEvent": EventSource.AUDIO,
        "PerformedNoteEvent": EventSource.SEGMENTER,
        "SessionEvent": EventSource.SESSION,
        "AlignedNote": EventSource.ALIGNMENT,
        "ScoreResult": EventSource.SCORING,
    }

    expected = rules.get(event_type)

    if expected is None:
        return

    if source != expected:
        raise RuntimeError(
            f"Invalid event flow: {event_type} emitted by {source}, expected {expected}"
        )
