# Violin Practice App — System Spec

| Status    | Version | Last Updated | Replaces | Historical Archive |
| :-------- | :------ | :----------- | :------- | :----------------- |
| **Draft** | v1.1.0  | June 2026    | N/A      | N/A                |

## 1. Overview

The system is a real-time audio processing pipeline that:

- captures microphone input
- estimates pitch continuously
- segments raw pitch into musical notes
- aligns performed notes with a target piece
- computes a final performance score at session end
- streams live feedback to a frontend via WebSockets

---

## 2. Core Design Principle

### Event Contract Ownership

Each pipeline stage owns the structure it emits.

Downstream stages may add information but should not reinterpret
or mutate the meaning of existing fields.

Examples:

- Pitch detection estimates frequency.
- Segmentation identifies stable note events.
- Alignment maps performed notes to expected notes.
- Scoring evaluates alignment results.

---

## 3. High-Level Architecture

```text
                ┌──────────────────────────┐
Microphone ───► │ PitchObservationEvent     │
                └─────────────┬────────────┘
                              ▼
                    NoteSegmenter (stateful)
                              │
          ┌───────────────────┴───────────────────┐
          ▼                                       ▼
Live path (real-time)                    Session path (batch)
          ▼                                       ▼
LiveDashboardMetrics                     PerformedNoteEvent
          ▼                                       ▼
WebSocket UI                           SessionController storage
                                                  ▼
                                       Alignment + Scoring Engine
                                                  ▼
                                          ScoreResult (end)
```

---

## 4. Time Model

### Time Source

All timing uses `time.perf_counter()`.

### Session Start

`SessionController.start_session()` records the reference timestamp.

### Relative Time

All timestamps stored after the ingestion layer are converted to
session-relative seconds.

#### Example:

```JSON
{
  "timestamp": 2.37
}
```

means:

```text
2.37 seconds after session start
```

---

## 5. Event Contracts

### PitchObservationEvent

Raw pitch detection output:

```python
class PitchObservationEvent(TypedDict):
    frequency: float
    note: str
    timestamp: float # Absolute machine time (time.perf_counter())
```

Produced by:

```python
AudioIngestionStream
```

Consumed by:

```python
NoteSegmenter
```

### PerformedNoteEvent

Stable musical note produced by segmentation.

```python
class PerformedNoteEvent(TypedDict):
    note: str
    frequency: float
    timestamp: float # Absolute machine time (time.perf_counter())
```

Produced by:

```python
NoteSegmenter
```

Consumed by:

```python
PracticeSession
Alignment
```

### LiveDashboardMetrics

Real-time UI payload.

```python
class LiveDashboardMetrics(TypedDict):
    frequency: float
    note: str
    time: float # Session-relative time (seconds)
    expected_note: Optional[str]
```

Produced by:

```python
process_notes
```

Consumed by:

```text
Frontend
```

### AlignedNote

Alignment output.

```python
class AlignedNote(TypedDict):
    expected_note: str
    performed_note: Optional[str]

    expected_time: float # Session-relative target time
    performed_time: Optional[float] # Session-relative performance time

    pitch_error_cents: Optional[float]
    time_error: Optional[float]

    match_quality: float
```

Produced by:

```python
align_notes()
```

Consumed by:

```python
score_alignment()
ScoreResult
```

### ScoreResult.

Final performance summary payload

```python
class ScoreResult(TypedDict):
    total_score: float
    pitch_accuracy: float
    timing_accuracy: float
    notes_hit: int
    notes_total: int
```

Produced by:

```python
ScoreEngine
```

Consumed by:

```text
Frontend
```

---

## 6. Pipeline Stages

### Stage 1 — Pitch Detection

#### Responsibilities:

- Read audio frames.
- Estimate frequency.
- Map frequency to nearest note.

Produces:

```python
PitchObservationEvent
```

Does NOT:

- Identify note boundaries.
- Score performance.
- Align notes.

### Stage 2 — Note Segmentation

#### Responsibilities:

- Convert pitch frames into stable note events.
- Remove rapid note flicker.
- Detect note transitions.

Produces:

```python
PerformedNoteEvent
```

Does NOT:

- Score notes.
- Compare against targets.

### Stage 3 — Session Pipeline

#### Responsibilities:

- Convert timestamps to session-relative time.
- Determine expected note at current time.
- Store session history.
- Emit websocket updates.

Produces:

```python
LiveDashboardMetrics
```

### Stage 4 — Alignment

#### Responsibilities:

- Match performed notes to expected notes.
- Compute timing differences.

Produces:

```python
AlignedNote
```

### Stage 5 — Scoring

#### Responsibilities:

- Compute pitch accuracy.
- Compute timing accuracy.
- Produce session score.

Produces:

```python
ScoreResult
```

---

## 7. Current Scoring Model (v1)

Pitch:

```text
Correct note = 1 point
Incorrect note = 0 points
```

Timing:

```python
1.0 - abs(error) / 0.4
```

clamped to:

```python
[0.0, 1.0]
```

Weighting:

```text
Pitch: 70%
Timing: 30%
```

---

## 8. Current Limitations

**Algorithmic:**

- Autocorrelation pitch estimation may misidentify notes.
- Alignment uses greedy nearest-neighbor matching.
- Timing tolerance is fixed at 400 ms.
- Pitch scoring is note-based rather than cents-based.

**System:**

- Sessions are stored in memory only.
- Piece definitions are hard-coded.
- No persistent score history.
- No session replay.

---

## Planned v2 Enhancements

- Add pitch_error_cents to PitchObservationEvent.
- Carry pitch accuracy through segmentation.
- Replace note-based pitch scoring with cents-based scoring.
- Persistent session storage.
- Session replay.
- Dynamic tempo-aware alignment.
- Confidence scoring.
- FFT or hybrid pitch detection.
