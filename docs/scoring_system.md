# Scoring System Design

## Overview & Project Scope

The long-term goal of the scoring system is to evaluate a player's performance against an expected musical target and provide meaningful feedback on accuracy and timing.

The scoring system is designed around common challenges faced by developing violinists, including intonation, rhythm, posture, and bow control.

The initial design of this scoring system is informed by the creator's personal experience learning the violin. As a result, the first set of performance metrics focuses on challenges that were encountered directly during practice, such as intonation, rhythm, posture, and bow control.

This should not be considered a comprehensive model of violin pedagogy. As the project evolves and feedback is gathered from other players and teachers, additional metrics and evaluation criteria may be introduced.

The long-term vision of the project is to evaluate multiple aspects of violin performance:

- Note accuracy
- Tempo accuracy
- Body alignment
- Bow alignment

The current scope of development is limited to audio-based evaluation, specifically note accuracy and tempo accuracy. Body and bow alignment are considered future extensions and are not part of the current scoring architecture.

Accessibility is a core design requirement. Performance feedback should not rely on red/green distinctions and should use a color scale that remains meaningful for colorblind users. Individual notes and performance metrics will be represented using a red-to-blue scale, allowing feedback to remain accessible while still providing an intuitive indication of performance quality.

Performance feedback will be presented across the following areas:

- Overall performance of the 4 areas combined
- Performance of note accuracy
- Performance of tempo accuracy
- Performance of body alignment
- Performance of bow alignment

Given this information, the player can pinpoint problem areas in a specific piece, and focus on the main issues that arise (intonation, clarity, tempo etc.)

Before these questions can be answered, the system must first determine what notes the player actually performed.

---

## System Architecture Overview

To generate meaningful performance feedback, the system processes audio input through a multi-stage execution pipeline. Each stage serves as a deterministic boundary, transforming the acoustic input into a progressively more structured and high-level representation of the musical performance.

```text
Audio Input
    ↓
[Stage 1] Pitch Detection
    ↓
[Stage 2] Note Segmentation
    ↓
[Stage 3] Sequence Alignment
    ↓
[Stage 4] Performance Evaluation
    ↓
[Stage 5] Score Aggregation & Reporting
```

Each stage operates with absolute separation of concerns, consuming the data structures emitted by the immediate upstream process.

---

## Stage 1: Pitch Detection (Ingestion Layer)

### Responsibility

Process raw digital audio frames to estimate the fundamental frequency ($f_0$) of the violin in real-time, outputting a continuous time-series stream of raw pitch observations alongside their deviation from equal temperament.

### Functional Characteristics

- **Sub-Musical Abstraction:** This layer does not interpret musical structure, note boundaries, or tempo. It functions purely as a mathematical frequency estimator and geometric error computer.

- **Granular Time-Series:** Outputs are generated at uniform intervals determined by the audio frame hops, providing high-density acoustic and precision data.

### Representation Data Example

The ingestion layer maps specific frequency bands to their closest musical note equivalents, computes deviation from equal temperament as diagnostic metadata ($1\text{ semitone} = 100\text{ cents}$), and records their absolute temporal positions:

```JSON
[
  { "note": "A4", "frequency": 440.12, "timestamp": 0.01, "pitch_error_cents": 0.5},
  { "note": "A4", "frequency": 439.85, "timestamp": 0.03, "pitch_error_cents": -0.6},
  { "note": "A4", "frequency": 440.01, "timestamp": 0.05, "pitch_error_cents": 0.0},
  { "note": "B4", "frequency": 493.52, "timestamp": 0.08, "pitch_error_cents": -1.3}
]
```

---

## Stage 2: Note Segmentation

### Responsibility

Convert continuous stream of raw pitch observations into stable, discrete musical note events.

### Input

Stream of pitch observations:

```python
(note, frequency, timestamp)
```

### Output

Performed notes:

```python
{
  note: int,
  start_time: float,
  end_time: float,
  confidence: float
}
```

### Core Requirement

A new note event is finalized and emitted only when:

- The observed pitch changes from the currently committed note AND
- the new pitch remains stable for a configurable threshold duration

### Design Principle

This stage acts purely as a temporal clustering filter for raw acoustic data. It is decoupled from any downstream musical evaluation, scoring, or tempo matching.

### Architectural Constraints & Limitations

- **Edge-Triggered Finalization:** Because note boundaries are determined by transitions, the final note of a performance session cannot be immediately finalized and emitted until either a new note/silence event is registered, or the performance session explicitly terminates.

### Architectural Evolution: Debouncing Pitch Jitter

An initial naive implementation tracked a single timestamp of the last detected note change. However, live acoustic streams from a violin contain high-frequency pitch jitter and transient noise during bow changes. The naive approach failed because brief, single-frame outliers corrupted the transition timer state.

To resolve this, the `NoteSegmenter` was refactored into a **2-State Confirmation Model** (a software debouncer):

1. **Committed State:** The note currently recognized as active and being sustained.
2. **Candidate State:** A new pitch detection under quarantine.

A candidate note must continuously persist across incoming audio frames for `>= stability_threshold` seconds before the state machine executes a transition, finalizes the previous note, and commits the new pitch. If the stream reverts to the committed note before the threshold is met, the candidate is discarded as background noise.

---

# To be reviewed

## Stage 3: Sequence Alignment

### Responsibility

Match performed notes to expected musical notes.

### Problem Type

This is a sequence alignment problem, not a direct comparison problem.

The system must handle:

- missed notes
- extra notes
- timing shifts
- imperfect detection boundaries

### Input

Expected notes:

```python
[{pitch, start_time}]
```

Performed notes:

```python
[{pitch, start_time, end_time}]
```

### Output

Aligned note pairs:

```python
[(expected_note, performed_note | None)]
```

### Design Note

Alignment is responsible for determining musical intent correspondence, not evaluating correctness.

---

## Stage 4: Performance Evaluation

Responsibility

Compute quantitative accuracy metrics for each aligned pair.

Metrics

Each aligned pair produces:

Pitch accuracy
Timing deviation
Confidence weighting

Example:

pitch_error = |expected_pitch - performed_pitch|
timing_error = |expected_time - performed_time|

Output

Per-note evaluation results:

{
pitch_score: float,
timing_score: float,
weighted_score: float
}

---

## Stage 5: Score Aggregation

Responsibility

Aggregate all evaluated notes into meaningful performance metrics.

Outputs

The system produces:

Overall performance score
Note accuracy score
Timing accuracy score
Missed note penalties
Extra note penalties
Design Principle

Scoring is aggregation-only.
It does not perform alignment or segmentation.

Accessibility Requirement

All performance feedback must avoid binary visual encoding (e.g. red/green only).

Instead, metrics should be represented using a continuous color scale (red → blue) to support colorblind accessibility and preserve gradient interpretation of performance quality.

Future Extensions (Non-Core Features)

The following features are explicitly out of scope for the current scoring system but may be added in future iterations:

Expressive Performance Analysis
vibrato detection
articulation analysis
bow pressure inference
phrasing detection
Physical Performance Analysis
posture tracking
bow alignment tracking
ergonomics feedback
Higher-Level Musical Intelligence
phrasing structure evaluation
stylistic interpretation scoring
teacher-style qualitative feedback
Key Design Principle

Each stage in the pipeline should be independently testable and replaceable.

No stage should depend on assumptions about internal logic of other stages—only their defined input/output contracts.

# Review End

---

## Challenge 1: Note Segmentation

### Problem Statement

The pitch detection system currently produces a continuous stream of pitch observations.

For example, if a player sustains an A4 for two seconds, the system may generate hundreds of observations:

```text
A4
A4
A4
A4
A4
A4
...
```

These observations are useful for pitch detection, but they do not represent musical notes.

For scoring purposes, the system must distinguish between:

- Raw pitch observations
- Performed musical notes

The scoring engine should operate on performed notes rather than individual observations.

---

### Example

A sustained note:

```text
Pitch Observations:
A4
A4
A4
A4
A4
```

Should become:

```text
Performed Notes:
A4
```

Similarly:

```text
Pitch Observations:
A4
A4
A4
B4
B4
B4
C#5
C#5
```

Should become:

```text
Performed Notes:
A4
B4
C#5
```

---

### Why This Matters

Without note segmentation, the scoring engine would incorrectly evaluate every pitch observation as a separate note event.

This would result in:

- Duplicate notes being counted repeatedly
- Incorrect timing calculations
- Inability to determine musical intent
- Poor scoring accuracy

A scoring system built directly on pitch observations would not accurately represent a player's performance.

---

### Initial Goal

The first version of note segmentation should identify distinct note changes.

A new note should be produced when the detected pitch changes and remains stable for a configurable period of time.

The initial implementation does not need to handle:

- Bow direction
- Slurs
- Articulation
- Dynamics
- Vibrato
- Musical phrasing

These can be introduced in future iterations.

---

## Proposed Architecture

Current pipeline:

```text
Audio Input
    ↓
Pitch Detection
    ↓
Pitch Observation
    ↓
Pipeline
```

Target pipeline:

```text
Audio Input
    ↓
Pitch Detection
    ↓
Pitch Observation
    ↓
Note Segmenter
    ↓
Performed Note
    ↓
Scoring Engine
```

The Note Segmenter becomes responsible for converting a continuous stream of pitch observations into discrete musical note events.

The Scoring Engine can then evaluate those note events against the expected target.

### Current Limitation

The current segmentation implementation emits a note when a note change
is detected.

As a result, the final note of a performance is not emitted until either:

- A subsequent note is played, or
- The session ends.

Future iterations will add explicit note-finalization logic to handle
the final note in a phrase.

---

## Future Challenges

Once note segmentation is complete, the scoring system will need to address:

### Challenge 2: Sequence Alignment

Determine how performed notes should be matched to expected notes.

Example:

```text
Expected:
A4
B4
C#5

Performed:
A4
C#5
```

The system must determine whether:

- B4 was missed entirely
- C#5 should be aligned with the third expected note
- Subsequent notes should be shifted accordingly

This is fundamentally a sequence alignment problem.

---

### Challenge 3: Timing Evaluation

Once notes are aligned, the system should evaluate timing accuracy.

Example:

```text
Expected:
A4 @ 0.0s
B4 @ 1.0s

Performed:
A4 @ 0.0s
B4 @ 1.2s
```

The system should measure the timing deviation and determine whether it falls within an acceptable tolerance.

---

### Challenge 4: Performance Scoring

After pitch and timing have been evaluated, aggregate performance metrics can be calculated, including:

- Note accuracy
- Timing accuracy
- Overall score
- Practice reports
- Progress tracking
- Historical comparisons

```

```
