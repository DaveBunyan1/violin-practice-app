from typing import List

from app.core.events import PitchObservationEvent
from app.services.note_segmenter import NoteSegmenter


def test_single_sustained_note():
    segmenter = NoteSegmenter(stability_threshold=0.1)

    output = []

    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.05},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.10},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.20},
    ]

    for e in events:
        segmenter.process(e)

    # no note change → no emission yet
    assert len(output) == 0


def test_note_change_emits_previous_note():
    segmenter = NoteSegmenter(stability_threshold=0.1)

    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.10},
        {"note": "B4", "frequency": 494.0, "timestamp": 0.25},
        {"note": "B4", "frequency": 494.0, "timestamp": 0.36},
    ]

    for e in events:
        segmenter.process(e)

    # should emit A4 when B4 is stable
    assert len(output) == 1
    assert output[0]["note"] == "A4"


def test_jitter_is_ignored():
    segmenter = NoteSegmenter(stability_threshold=0.1)

    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00},
        {"note": "A#4", "frequency": 466.0, "timestamp": 0.05},  # jitter
        {"note": "A4", "frequency": 440.0, "timestamp": 0.08},  # back
        {"note": "A4", "frequency": 440.0, "timestamp": 0.20},
    ]

    for e in events:
        segmenter.process(e)

    assert len(output) == 0


def test_stability_threshold_boundary():
    segmenter = NoteSegmenter(stability_threshold=0.1)

    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00},
        {"note": "B4", "frequency": 494.0, "timestamp": 0.09},  # just below threshold
        {"note": "B4", "frequency": 494.0, "timestamp": 0.15},  # stable now
    ]

    for e in events:
        segmenter.process(e)

    # should NOT emit A4 yet (still within jitter window)
    assert len(output) == 0


def test_first_note_is_not_emitted():
    segmenter = NoteSegmenter(stability_threshold=0.1)

    output = []
    segmenter.set_callback(output.append)

    segmenter.process({"note": "A4", "frequency": 440.0, "timestamp": 0.0})

    assert len(output) == 0


def test_vibrato_does_not_prematurely_trigger_emission():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    # Pitch rapidly wiggles every 0.04 seconds (under the 0.1 threshold)
    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00},
        {"note": "A#4", "frequency": 466.0, "timestamp": 0.04},  # Wiggle sharp
        {"note": "A4", "frequency": 440.0, "timestamp": 0.08},  # Wiggle back
        {"note": "A#4", "frequency": 466.0, "timestamp": 0.12},  # Wiggle sharp
        {"note": "A4", "frequency": 440.0, "timestamp": 0.16},  # Wiggle back
    ]

    for e in events:
        segmenter.process(e)

    # Because no single candidate held for >= 0.1s, nothing should emit
    assert len(output) == 0


def test_candidate_overwritten_by_different_candidate():
    segmenter = NoteSegmenter(stability_threshold=0.1)

    output = []
    segmenter.set_callback(output.append)

    # Timeline Scenario:
    # 0.00: Player plays stable A4
    # 0.08: A quick accidental scrape registers as B4 (Candidate 1 starts)
    # 0.12: Player cleanly lands on C5 (Candidate 2 overwrites B4)
    # 0.23: C5 has now been stable for 0.11s (0.23 - 0.12 >= 0.1 threshold) -> Emits A4
    # 0.40: Player transitions to D5, forcing the finalized C5 to emit
    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00},
        {"note": "B4", "frequency": 494.0, "timestamp": 0.08},
        {"note": "C5", "frequency": 523.2, "timestamp": 0.12},
        {"note": "C5", "frequency": 523.2, "timestamp": 0.23},
        {"note": "D5", "frequency": 587.3, "timestamp": 0.40},
        {"note": "D5", "frequency": 587.3, "timestamp": 0.55},
    ]

    for e in events:
        segmenter.process(e)

    # We expect 2 notes to be emitted: A4 and C5
    assert len(output) == 2

    # First emission should be the initial A4 note
    assert output[0]["note"] == "A4"
    assert output[0]["timestamp"] == 0.00

    # Second emission should be the C5 note
    c5_note = output[1]
    assert c5_note["note"] == "C5"

    # CRUCIAL TEST: The onset timestamp of C5 must be exactly 0.12
    # (when C5 first arrived), NOT 0.08 (when the transient B4 arrived).
    assert c5_note["timestamp"] == 0.12


#
def test_silence_finalizes_previous_note():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.10},
        {"note": "REST", "frequency": 0.0, "timestamp": 0.20},  # Player stops bowing
        {"note": "REST", "frequency": 0.0, "timestamp": 0.31},  # Rest is stable
    ]

    for e in events:
        segmenter.process(e)

    # The rest finalized the A4 note event
    assert len(output) == 1
    assert output[0]["note"] == "A4"


def test_identical_timestamps_do_not_cause_accidental_stability():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00},
        {"note": "B4", "frequency": 494.0, "timestamp": 0.05},
        {
            "note": "B4",
            "frequency": 494.0,
            "timestamp": 0.05,
        },  # Duplicate/rapid timestamp
    ]

    for e in events:
        segmenter.process(e)

    assert len(output) == 0


def test_final_note_is_flushed_on_end():
    segmenter = NoteSegmenter(stability_threshold=0.1)
    output = []
    segmenter.set_callback(output.append)

    events: List[PitchObservationEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.10},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.30},
    ]

    for e in events:
        segmenter.process(e)

    # simulate end of stream
    segmenter.flush(0.31)

    assert len(output) == 1
    assert output[0]["note"] == "A4"
