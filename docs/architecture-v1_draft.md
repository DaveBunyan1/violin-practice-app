# Violin Practice App — System Spec

| Status    | Version | Last Updated | Replaces | Historical Archive |
| :-------- | :------ | :----------- | :------- | :----------------- |
| **Draft** | v1.0.0  | June 2026    | N/A      | N/A                |

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

## 7. Event Contract Table (v1)

## 7.1 Design Rules (Applies to All Events)

- Each event has a single producer
- Each field has a fixed semantic meaning
- Timestamps are never overloaded with multiple meanings
- Downstream layers may add derived events, but must not mutate existing ones
- REST is treated as a valid musical state, not noise (unless explicitly filtered earlier)

## 7.2 PitchObservationEvent (Ingestion Layer)

**Purpose:** Raw pitch estimation output from audio frames

```python
class PitchObservationEvent(TypedDict):
    frequency: float
    note: str
    timestamp: float  # PERF_COUNTER (absolute monotonic time)
```

#### Produced by

- AudioIngestionStream

#### Consumed by

- NoteSegmenter

#### Rules

- Must NOT contain session-relative time
- Must NOT contain alignment or scoring data
- May include "REST" as valid note state

## 7.3 PerformedNoteEvent (Segmentation Layer)

**Purpose:** Stable musical note extracted from raw pitch stream

```python
class PerformedNoteEvent(TypedDict):
note: str
frequency: float
timestamp: float # PERF_COUNTER (note onset time)

```

#### Produced by

- NoteSegmenter

#### Consumed by

- Session storage
- Alignment engine

#### Rules

- Represents a musical decision, not raw audio
- Must be stable (debounced / confirmed)
- Must NOT include pitch estimation metadata (unless explicitly extended later)

## 7.4 LiveDashboardMetrics (Realtime UI Layer)

**Purpose:** Real-time feedback stream for frontend visualization

```python
class LiveDashboardMetrics(TypedDict):
    frequency: float
    note: str
    time: float  # session-relative time
    expected_note: Optional[str]
```

#### Produced by

- Pipeline orchestrator (process_notes)

#### Consumed by

- Frontend WebSocket UI

#### Rules

- Must always use session-relative time
- Must NOT be used for scoring
- May include derived fields (expected note, error hints later)

## 7.5 AlignedNote (Alignment Layer)

**Purpose:** Mapping between performed notes and expected score positions

```python
class AlignedNote(TypedDict):
    expected_note: str
    performed_note: Optional[str]

    expected_time: float  # score timeline reference
    performed_time: Optional[float]  # session-relative

    pitch_error_cents: Optional[float]
    time_error: Optional[float]

    match_quality: float
```

#### Produced by

- align_notes()

#### Consumed by

- ScoreEngine

#### Rules

- Must NOT modify performed data
- Must NOT recompute pitch detection
- Alignment is purely a mapping function

## 7.6 ScoreResult (Scoring Layer)

**Purpose:** Final evaluation of session performance

```python
class ScoreResult(TypedDict):
    total_score: float
    pitch_accuracy: float
    timing_accuracy: float
    notes_hit: int
    notes_total: int
```

#### Produced by

- ScoreEngine

#### Consumed by

- Frontend (end-of-session)

#### Rules

- Pure output only
- Must not retain session state
- Must not mutate alignment data

## 7.7 Session Internal Events (Implementation Detail)

These are NOT external contracts but important for clarity:

```python
PracticeSession.events
PracticeSession.performed_notes
```

#### Rules

- Internal storage only
- May diverge from external event schemas for optimization
- Never exposed directly to frontend

---

## 8. Contract Flow Diagram (v1 tightened)

```text
AudioIngestionStream
    ↓
PitchObservationEvent
    ↓
NoteSegmenter
    ↓
PerformedNoteEvent
    ↓
Pipeline Orchestrator
    ├── LiveDashboardMetrics → WebSocket UI
    └── Session storage
             ↓
        Alignment Engine
             ↓
         AlignedNote
             ↓
        ScoreEngine
             ↓
         ScoreResult
```

## 9. Current Scoring Model (v1)

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

## 10. Current Limitations

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
