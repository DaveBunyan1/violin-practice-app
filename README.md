# Violin Practice App

A real-time violin practice system that captures microphone audio, estimates pitch, segments notes, aligns them against a target piece, and streams live feedback alongside a final performance score.

This is **v1** — a working end-to-end proof of concept that taught me a great deal about real-time audio pipelines, event-driven design, telemetry, and the cost of architectural shortcuts. Those lessons directly shaped the architecture of my subsequent project, the [Chinese Vocabulary Training](https://github.com/DaveBunyan1/chinese-vocabulary-training) platform (Domain-Driven Design + Hexagonal Architecture).

I am now circling back to apply what I learned from the Chinese app, _High Performance Python_, _Fluent Python_, and my own experience as a violin student to a clean **v2**.

> **Key documents**
>
> - [Engineering Retrospective (Chinese app)](https://github.com/DaveBunyan1/chinese-vocabulary-training/blob/main/docs/reflections/0001_violin_app_lessons.md)
> - [`docs/LEARNINGS.md`](docs/LEARNINGS.md) — deeper reflection on product insights, telemetry, and the “make it work → make it right → make it fast” progression
> - [`docs/architecture.md`](docs/architecture.md) · [`docs/telemetry.md`](docs/telemetry.md) · [`docs/journey.md`](docs/journey.md)

---

## Why This Project Exists

As a violin student I repeatedly hit the same problems:

- Practising without immediate, objective feedback on pitch and timing
- Difficulty knowing _which_ bars, notes, or technical elements needed the most attention
- Limited ability to measure whether repeated practice was actually improving performance
- An overall impression of a performance that obscured specific recurring weaknesses

The original goal was simple: build something that could listen to me play and give objective feedback.

What quickly became clear, however, is that music does not map perfectly onto a purely mathematical representation. Perfect pitch and timing are useful targets, but aiming to turn a human player into a flawless “human metronome” is neither realistic nor musically desirable. Version 1 of the app leans too heavily in that direction.

Many of the changes planned for v2 are therefore deliberately personal. Being left-handed is the single largest practical constraint on my own technique, so greater attention will be given to bowing, string crossings, and related physical aspects of playing. At the same time, the broader design is informed by lessons from building the Chinese Vocabulary Training app and from my own experience learning both the violin and Chinese: progress is usually made by focusing on the specific things one currently struggles with, rather than by repeatedly evaluating complete performances.

The intention is not to replace traditional or accepted musical pedagogy. The app should remain an addition to learning — a sometimes harsh, still-naïve teacher that can highlight problems and track improvement — rather than a substitute for a real teacher, a method book, or deliberate practice away from the screen. Ideally, a student should still be able to practise a scale, a bar, a passage, or an entire piece effectively without the application running at all.

v1 ultimately became as much a learning project in software engineering as it was a violin practice tool. That dual purpose continues into v2.

---

## Current Capabilities — v1

- Live microphone capture (`sounddevice`)
- Pitch estimation via autocorrelation
- Note segmentation (debouncing + state machine)
- Real-time WebSocket feedback to a Next.js frontend
- Alignment of performed notes against a target piece
- End-of-session scoring (pitch + timing)
- Basic repertoire management and BPM control
- Persistence of sessions and pieces
- Early telemetry and benchmarking harness

```text
Microphone → Pitch estimation → Note segmentation → Alignment → Scoring
                ↓
          Live feedback + final analysis
```

See [`docs/architecture.md`](docs/architecture.md) for the full event contracts and pipeline design.

---

## Architecture Snapshot — v1

```text
Microphone
    ↓
PitchObservationEvent
    ↓
NoteSegmenter
    ↓
PerformedNoteEvent
    ├──→ Live feedback / WebSocket dashboard
    └──→ Session / alignment / scoring
```

The system uses events to separate the different stages of the pipeline, but v1 also contains architectural compromises that became increasingly apparent as the project grew.

The evolution of those decisions is documented in:

- [`docs/architecture.md`](docs/architecture.md) — current v1 architecture and event contracts
- [`docs/telemetry.md`](docs/telemetry.md) — performance and telemetry work
- [`docs/journey.md`](docs/journey.md) — chronological engineering narrative
- [`docs/past_architecture/`](docs/past_architecture/) — earlier architectural iterations

---

## What I Learned from v1 (Summary)

Building a system that could evaluate an entire performance was technically satisfying. Using it as the intended user revealed a more important product insight:

> A final score does not necessarily tell me **what I should practise next**.

My weaknesses as a violin student are granular — particular notes, passages, rhythmic problems, intonation issues, consistency. Reducing the whole performance to a single number can obscure the very information that would make practice more effective.

This shifted the design goal for v2 from:

> “How well did I perform this piece?”

towards:

> “What specifically should I practise, and is that area improving?”

This is a product insight derived from using the application myself, not a claim of formal pedagogical research. The full reflection is in [`docs/LEARNINGS.md`](docs/LEARNINGS.md).

Telemetry also changed how I think about the system. Final scores can look reasonable while intermediate stages are silently discarding frames. That led to treating observability as an architectural concern rather than an afterthought.

---

## From “Make It Work” to “Make It Right” to “Make It Fast”

v1 successfully demonstrated that the complete pipeline can function in real time. It is firmly in the **make it work** category.

v2 is an opportunity to move deliberately through the next two stages, guided by the hard real-time constraint of the application:

```text
Maximum processing latency per frame < ~46.44 ms
```

(The available budget for a 2048-sample buffer at 44.1 kHz.)

The performance objective is therefore **not** “minimise latency at any cost.” It is:

> Stay below the real-time latency constraint while making sensible trade-offs between latency, memory usage, and implementation complexity.

The longer discussion of this philosophy, the value of measuring maximum rather than only average latency, and the planned experimental approach to optimisation lives in [`docs/LEARNINGS.md`](docs/LEARNINGS.md).

---

## Lessons That Shaped the Chinese App (and will shape Violin v2)

| Friction in Violin v1                               | Response in Chinese App / Violin v2                              |
| --------------------------------------------------- | ---------------------------------------------------------------- |
| Business logic mixed with audio callbacks           | Domain logic separated from infrastructure via ports & adapters  |
| Global state and circular imports                   | Explicit dependency injection + composition root                 |
| Tests retrofitted around existing code              | Tests designed around isolated domain behaviour                  |
| Observability added late                            | Telemetry and structured logging treated as first-class concerns |
| Naïve benchmarking that could not support decisions | Controlled performance harnesses + statistical thinking          |
| Hard-coded pieces / in-memory assumptions           | Persistent, queryable domain models                              |
| Infrastructure details leaking into core logic      | Explicit boundaries between domain and infrastructure            |

The Chinese application was, in part, an opportunity to take the problems discovered here and learn how to avoid them. v2 now brings those lessons back.

---

## Roadmap — v2

The full prioritised list with rationale will live in `docs/ROADMAP-v2.md`. High-level summary:

**Architecture**

- Hexagonal / Clean Architecture redesign
- Audio input behind an `AudioStreamInputPort` + synthetic/recorded adapters for deterministic testing
- Explicit dependency graph and composition root (no global state)
- Clear separation of the real-time path from offline analysis

**Audio & Pitch Detection**

- Replace naïve autocorrelation with a more robust, measurable approach
- Keep pitch detection behind a swappable interface
- Establish accuracy benchmarks using controlled recordings

**Performance**

- Formal frame-processing budget focused on **maximum** latency
- Controlled offline performance harness
- Allocation behaviour, vectorisation, and hot-path work only when measurements justify it

**Practice & Learning**

- Shift from “how well did I perform?” to “what should I practise next?”
- Focus modes (specific bars, technical elements, slow practice, drone)
- Note-level error analysis, session replay, improvement tracking
- Adaptive recommendations based on historical errors

**Quality & Developer Experience**

- Comprehensive unit + integration tests with synthetic audio fixtures
- Root `Makefile` (`make test`, `make bench`, `make lint`, etc.)
- CI with performance regression awareness
- Architecture Decision Records for significant decisions

---

## Tech Stack

| Layer       | Technology                                                 |
| ----------- | ---------------------------------------------------------- |
| Backend     | Python, FastAPI, SQLAlchemy                                |
| Audio / DSP | NumPy, SciPy, sounddevice                                  |
| Frontend    | Next.js 16, React 19, TypeScript, Tailwind CSS 4, Recharts |
| Real-time   | WebSockets                                                 |
| Testing     | Pytest + coverage                                          |

---

## Development

The development workflow is being revised as part of v2. Current setup:

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm run dev
```

The eventual v2 workflow will be consolidated around a root-level `Makefile`.

---

## Related Projects

**Chinese Vocabulary Training**  
https://github.com/DaveBunyan1/chinese-vocabulary-training

A Chinese-learning platform that became the primary beneficiary of the architectural lessons learned while building this application. It uses Domain-Driven Design and Hexagonal Architecture.

Retrospective documenting the relationship:  
[Engineering Retrospective: Lessons from the Violin App](https://github.com/DaveBunyan1/chinese-vocabulary-training/blob/main/docs/reflections/0001_violin_app_lessons.md)

---

## Status

**v1 is feature-complete as a learning vehicle and personal practice tool.**

The existing implementation successfully demonstrates the complete real-time pipeline from microphone input through pitch detection, note segmentation, alignment, scoring, and live feedback.

```text
v1 (Make it work)
    ↓
Lessons learned → Chinese Vocabulary Training
    ↓
High Performance Python / Fluent Python
    ↓
v2 (Make it right → Measure → Make it fast)
```

The goal is not simply to produce a technically impressive violin-analysis application. It is to build a system that is **useful to a violin student**, while using the project to explore real-time audio processing, software architecture, observability, performance engineering, and the trade-offs between correctness, maintainability, developer velocity, and performance.

---

Built as a deliberate practice project — both for the violin and for software engineering.
