# Violin Practice App — System Spec

| Status       | Version                | Last Updated | Replaces | Historical Archive |
| :----------- | :--------------------- | :----------- | :------- | :----------------- |
| **Approved** | v0.1.0 (Current State) | June 2026    | N/A      | N/A                |

## 1. Overview

The system is a real-time audio processing pipeline that:

- captures microphone input
- estimates pitch continuously
- segments raw pitch into musical notes
- aligns performed notes with a target piece
- computes a final performance score at session end
- streams live feedback to a frontend via WebSockets

---

## 2. High-Level Architecture

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

## 3. System Components

### 3.1 Audio Ingestion Layer

#### Responsibility

Convert raw audio frames into pitch estimates in real time.

#### Implementation

- sounddevice callback stream
- autocorrelation-based frequency estimation (current)
- note mapping via freq_to_note

#### Output Event

```python
class PitchObservationEvent(TypedDict):
    frequency: float
    note: str
    timestamp: float  # time from perf_counter()
```

#### Notes

- REST detected as "REST" note
- timing uses `time.perf_counter()`
- no musical structure is inferred here

---

### 3.2 Note Segmentation Layer

#### Component

`NoteSegmenter`

#### Responsibility

Convert noisy pitch stream into stable musical note events.

#### Behaviour

- maintains internal state (current + candidate note)
- confirms notes after stability threshold (~100ms default)
- emits note start events via callback

#### Output Event

```python
class PerformedNoteEvent(TypedDict):
    note: str
    frequency: float
    timestamp: float  # note onset time
```

#### Notes

- REST notes are currently emitted but not always used downstream
- segmentation is stateful and time-based only
- no reference to target piece

---

### 3.3 Session Model

#### Component

`PracticeSession`

#### Responsibility

Store all session-related data during a practice run.

#### Stored Data

```python
start_time: float
events: List[LiveDashboardMetrics]
performed_notes: List[PerformedNoteEvent]
```

#### Notes

- thread-safe via RLock
- start time uses `time.perf_counter()`
- acts as in-memory event log

---

### 3.4 Session Controller

#### Component

`SessionController`

#### Responsibility

Manage lifecycle of a practice session.

#### Features

- `start_session()`
- `reset_session()`
- `get_session()`

#### Notes

- only one active session at a time
- protects session with lock

---

### 3.5 Pipeline (Alignment Stage)

#### Component

`process_notes`

#### Responsibility

Transform performed notes into live metrics + session storage.

#### Inputs

```python
PerformedNoteEvent
```

#### Outputs

1. Session storage update (`session.add_event`)
2. Live dashboard event via WebSockets

#### Live Event

```python
class LiveDashboardMetrics(TypedDict):
    frequency: float
    note: str
    time: float  # relative time
    expected_note: Optional[str]
```

#### Behaviour

- blocks on the `inbound_queue` waiting for the upstream segmenter to confirm a stable note.
- computes relative time using session start
- queries the expected note from PracticeTarget for that specific time snapshot
- stores the metrics in the session log
- broadcasts the note data down the WebSocket for the UI dashboard

---

### 3.6 Practice Target (Piece Definition)

#### Component

`PracticeTarget`

#### Responsibility

Define expected notes for a session.

#### Modes

- tuner (single note)
- piece (sequence of notes)

#### Example

```python
ExpectedNote("G3", 1)
ExpectedNote("D4", 2)
ExpectedNote("A4", 3)
ExpectedNote("E5", 4)
```

#### Behaviour

- maps time → expected note
- used only during alignment stage

---

### 3.7 Alignment + Scoring Engine

#### Component

`ScoreEngine`

#### Responsibility

Convert session performance into a final score.

#### Pipeline

```text
Expected notes + Performed notes
        ↓
Alignment (note matching by time)
        ↓
Score computation
        ↓
ScoreResult
```

#### Output

```python
class ScoreResult(TypedDict):
    total_score: float
    pitch_accuracy: float
    timing_accuracy: float
    notes_hit: int
    notes_total: int
```

#### Notes

- alignment currently uses greedy time-based matching
- scoring uses pitch match + timing error
- invoked manually via end_session

---

### 3.8 WebSocket Layer

#### Responsibility

Provide real-time UI updates + session control.

#### Incoming Messages

```JSON
{ "type": "start_session" }
{ "type": "reset_session" }
{ "type": "end_session" }
```

#### Outgoing Messages

- live pitch stream (`LiveDashboardMetrics`)
- final score (on end session)

---

## 4. Timing System

### Current Implementation

- `time.perf_counter()` used everywhere
- relative time computed as:

```python
relative_time = event.timestamp - session.start_time
```

### Known Behaviour

- stable for short sessions
- drift-free relative consistency
- not persistent across sessions

---

## 5. Data Flow Summary

### Live Path (real-time feedback)

```text
PitchObservationEvent
    ↓
NoteSegmenter
    ↓
LiveDashboardMetrics
    ↓
WebSocket UI
```

```text
Session Path (evaluation)
PitchObservationEvent
    ↓
NoteSegmenter
    ↓
PerformedNoteEvent
    ↓
SessionController storage
    ↓
ScoreEngine (on end_session)
    ↓
ScoreResult
```

---

## 6. Known Limitations (v0)

### DSP

- autocorrelation may misdetect harmonics
- noise handling is basic

### Segmentation

- REST handling is inconsistent
- no explicit note end timestamps (important limitation)

### Alignment

- greedy matching (not optimal for complex rhythms)
- assumes near-linear progression

### Scoring

- simple weighting model
- no expressive features (vibrato, articulation, etc.)

---

## 7. Design Intent (NOT implemented yet)

These are future directions only:

- FFT-based pitch detection (replace autocorrelation)
- persistent session storage (replayable sessions)
- strict event contracts per layer
- improved alignment (DP / HMM-based)
- richer scoring model (intonation curves, stability metrics)

---

## 8. Core Design Principle (v0)

<br/>

> [!NOTE]
> Each layer transforms data exactly once and adds structure — it does not reinterpret prior meaning.
