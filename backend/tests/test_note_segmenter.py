from typing import List

from app.core.events import NoteEvent
from app.services.note_segmenter import NoteSegmenter


def test_single_sustained_note():
    segmenter = NoteSegmenter(stability_threshold=0.1)

    output = []

    segmenter.set_callback(output.append)

    events: List[NoteEvent] = [
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

    events: List[NoteEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00},
        {"note": "A4", "frequency": 440.0, "timestamp": 0.10},
        {"note": "B4", "frequency": 494.0, "timestamp": 0.25},
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

    events: List[NoteEvent] = [
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

    events: List[NoteEvent] = [
        {"note": "A4", "frequency": 440.0, "timestamp": 0.00},
        {"note": "B4", "frequency": 494.0, "timestamp": 0.09},  # just below threshold
        {"note": "B4", "frequency": 494.0, "timestamp": 0.20},  # stable now
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
