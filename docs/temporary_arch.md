# Scoring System Architecture

## Overview & Project Scope

This scoring system is an engineering prototype designed to evaluate a violinist's performance against a target musical score. Developed as a personal training tool and a technical portfolio piece, the project focuses on solving complex audio signal processing (DSP) and sequence alignment problems.

Rather than building a generalized commercial application, the scope of this project is deliberately constrained to the immediate pedagogical needs of the developer: **intonation (pitch accuracy)** and **rhythm (tempo accuracy)**.

Future extensions—such as computer vision models for body and bow alignment—are mapped out conceptually to demonstrate architectural scalability, but the core implementation focuses strictly on audio-based metrics.

---

## Technical Design Pillars

### 1. Objective, Accessible UX

A core requirement of the feedback loop is data clarity. To ensure the interface is highly scannable during practice sessions, performance metrics avoid traditional red/green color paradigms. Instead, the UI implements a high-contrast, colorblind-friendly **red-to-blue scale** to map deviations in pitch and time, establishing accessibility as a baseline constraint rather than an afterthought.

Feedback is aggregated into two distinct layers to maximize utility for a practicing musician:

- **Composite Performance Score:** A macro-level reflection of overall execution.
- **Isolatable Micro-Metrics:** Granular breakdowns of pitch vs. timing, allowing the player to debug specific failure modes (e.g., separating a finger-placement error from a rhythmic rushing habit).

### 2. The Sequential Execution Pipeline

To transform raw acoustic data into actionable feedback, the system architecture executes a strict, six-stage sequential pipeline. Each stage serves as a deterministic boundary, feeding data directly into the next.

[1. Note Segmentation] ➔ [2. Sequence Alignment] ➔ [3. Pitch Evaluation]
⬇
[6. UI/UX Presentation] 🡨 [5. Metric Aggregation] 🡨 [4. Timing Evaluation]

1. **Note Segmentation:** DSP-driven detection to isolate discrete note events from a continuous audio stream.
2. **Sequence Alignment:** Dynamic programming algorithms to map the performed event sequence to the expected ground-truth musical score.
3. **Pitch Evaluation:** Estimating fundamental frequency ($f_0$) to measure precise cent deviations from equal temperament.
4. **Timing Evaluation:** Comparing realized note boundaries against the score's temporal structure.
5. **Metric Aggregation:** Normalizing error rates into standardized, display-ready data structures.
6. **UI Presentation:** Rendering accessible visual markers back to the user.

---

## Current Engineering Focus: Note Segmentation

While the end goal is comprehensive performance evaluation, downstream stages (alignment, pitch tracking, and timing metrics) are entirely dependent on clean input boundaries. Because the system cannot analyze a performance until it can reliably identify when notes begin and end, **Note Segmentation** represents the primary algorithmic bottleneck and the first major engineering challenge documented below.
