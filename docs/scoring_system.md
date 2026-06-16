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

To generate meaningful performance feedback, the system processes audio input through a multi-stage pipeline. Each stage produces a progressively more structured representation of the performance.

```text
Audio Input
    ↓
Pitch Detection
    ↓
Note Segmentation
    ↓
Sequence Alignment
    ↓
Performance Evaluation
    ↓
Score Aggregation & Reporting
```

Each stage has a clearly defined responsibility and produces an output consumed by the next stage.

---

## Stage 1: Pitch Detection (Existing System)

The pitch detection layer produces a continuous stream of pitch observations.

These observations are time-stamped frequency estimates, not musical notes.

Example output:

```text
(A4, t=0.01)
(A4, t=0.03)
(A4, t=0.05)
(B4, t=0.80)
```

This layer does not interpret musical structure.

---

## Stage 2: Note Segmentation

#### Responsibility

Convert continuous pitch observations into discrete musical note events.

#### Input

Stream of pitch observations:

```python
(pitch, timestamp)
```

#### Output

Performed notes:

```python
{
  pitch: int,
  start_time: float,
  end_time: float,
  confidence: float
}
```

#### Core Requirement

A new note is created when:

- pitch changes AND
- the new pitch remains stable for a configurable threshold duration

#### Design Principle

This stage performs temporal clustering of pitch data, not scoring or evaluation.

Important Limitation

- The final note in a performance may not be immediately closed until:

- a new note is detected, or
  the session ends

---

# To be reviewed

Stage 3: Sequence Alignment
Responsibility

Match performed notes to expected musical notes.

Problem Type

This is a sequence alignment problem, not a direct comparison problem.

The system must handle:

missed notes
extra notes
timing shifts
imperfect detection boundaries
Input

Expected notes:

[{pitch, start_time}]

Performed notes:

[{pitch, start_time, end_time}]
Output

Aligned note pairs:

[
(expected_note, performed_note | None)
]
Design Note

Alignment is responsible for determining musical intent correspondence, not evaluating correctness.

Stage 4: Performance Evaluation
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
Stage 5: Score Aggregation
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
