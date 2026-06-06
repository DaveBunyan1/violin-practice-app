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

To produce meaningful feedback, the system must solve several problems in sequence.

1. Determine which notes were actually performed.
2. Align performed notes with expected notes.
3. Evaluate pitch accuracy.
4. Evaluate timing accuracy.
5. Aggregate results into performance metrics.
6. Present feedback to the player.

Each stage depends on the successful completion of the previous stage.

Although the end goal is performance evaluation, the system cannot evaluate a performance until it can reliably identify the individual notes that were played. For this reason, note segmentation is the first challenge to solve.

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
