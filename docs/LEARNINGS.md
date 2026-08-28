# Engineering & Product Learnings from Violin Practice App v1

This document captures the deeper reflections that emerged while building and using v1.  
The README summarises the high-level story; this file is the detailed record.

---

## 1. Product Insight: A Score Is Not a Practice Plan

I initially focused heavily on the technical challenge of evaluating an entire performance.

That is useful: being able to play a piece and receive an objective score for pitch and timing provides a meaningful measure of performance.

However, actually using the application exposed a more important problem.

A final score does not necessarily tell me **what I should practise next**.

My weaknesses as a violin student are more granular. Particular notes, passages, rhythmic problems, intonation issues, consistency, or other musical elements can be obscured when the entire performance is reduced to a single score.

This became particularly apparent when comparing the problem with my Chinese-learning application.

I am not a language teacher and do not claim formal pedagogical expertise, but I have spent enough time learning Chinese to have a reasonable understanding of its grammar and some of the common difficulties encountered by learners. That makes it easier for me to recognise when a language-learning feature is failing to address the actual problem.

The violin application exposed the opposite situation: I could build an end-to-end evaluation system without necessarily measuring the things that were most useful to me as a learner.

That distinction will be an important design constraint for v2.

The goal is therefore moving from:

> **"How well did I perform this piece?"**

towards:

> **"What specifically should I practise, and is that area improving?"**

This is not presented as a conclusion from formal pedagogical research. It is a product insight derived from using the application as its intended user.

---

## 2. Telemetry Revealed What the Final Score Hid

The telemetry work in v1 also revealed problems that were difficult to see from the final output alone.

For example, fewer audio frames than expected were making it through the `NoteSegmenter`, while additional frames were being rejected by downstream constraints.

This matters because a final performance score can look reasonable while the underlying pipeline is silently discarding information.

That led to a broader lesson:

> **End-to-end correctness is not enough for a real-time system; the behaviour of the intermediate stages needs to be observable.**

Telemetry therefore becomes part of the architecture rather than something added after the application appears to work.

---

## 3. From “Make It Work” to “Make It Right” to “Make It Fast”

One of the principles from _High Performance Python_ that has particularly influenced how I am approaching v2 is the progression:

> **Make it work. Make it right. Make it fast.**

v1 is firmly in the **make it work** category.

It demonstrates that the complete pipeline can function in real time, but it also contains architectural shortcuts, incomplete abstractions, and performance assumptions that were made while the system was still being understood.

v2 is an opportunity to approach the project differently.

### Make it work

Already demonstrated by v1:

```text
Microphone
    ↓
Pitch detection
    ↓
Note segmentation
    ↓
Alignment
    ↓
Scoring
    ↓
Feedback
```

### Make it right

The next priority is to establish:

- Clear domain boundaries
- Explicit dependencies
- Testable components
- Deterministic audio-processing tests
- Reliable telemetry
- Well-defined event contracts
- A measurable real-time performance budget
- A product model that reflects the actual needs of a practising musician

Correctness in v2 therefore includes more than simply producing the right final score.

It also means ensuring that the architecture makes the system understandable, testable, observable, and capable of evolving.

### Make it fast

Only after the behaviour and architecture are sufficiently well understood should performance optimisation become the focus.

However, this application has an unusual constraint: **real-time processing gives performance a hard upper bound.**

---

## 4. The 46.44 ms Constraint

The application processes audio in frames with approximately **46.44 ms available per frame** (2048 samples at 44.1 kHz).

This creates a hard real-time requirement:

```text
Maximum processing latency < 46.44 ms
```

The important word here is **maximum**.

For a real-time audio pipeline, an implementation with a very low average latency but occasional processing spikes beyond the available budget is not necessarily better than an implementation with a higher but predictable latency.

Conceptually:

```text
1 MB memory / 42 ms maximum latency
>
10 MB memory / 29 ms maximum latency
```

if both satisfy the application’s requirements and the additional memory provides no useful benefit.

Likewise:

```text
1 KB memory / 30 ms average latency
```

is not necessarily preferable if it occasionally produces processing spikes close to or beyond the 46.44 ms real-time budget.

The performance objective is therefore not:

> **Minimise latency at any cost.**

It is:

> **Stay below the real-time latency constraint while making sensible trade-offs between latency, memory usage, and implementation complexity.**

This also provides a concrete way to apply the broader principle of **avoiding premature optimisation**.

If an implementation already satisfies the real-time requirement, reducing its memory usage or average latency is an engineering experiment rather than an automatic product improvement.

---

## 5. Performance as an Engineering Experiment

I am still working through _High Performance Python_, so v2 will also be an opportunity to experiment with the techniques discussed there rather than applying them mechanically.

The intention is to investigate performance progressively:

```text
Correct implementation
    ↓
Measure
    ↓
Identify bottleneck
    ↓
Improve algorithm / architecture
    ↓
Measure again
    ↓
Optimise hot path where justified
    ↓
Measure again
```

Potential areas of investigation include:

- Better algorithmic complexity
- Reducing unnecessary allocations
- More efficient NumPy operations
- Vectorisation
- Memory layout and data representation
- Avoiding unnecessary copies
- Concurrency where workloads are genuinely independent
- Separating real-time work from non-real-time work
- Lower-level implementations when measurements justify the additional complexity

For example, if a future pitch-detection implementation moves from autocorrelation towards a more computationally expensive combination such as CQT and CREPE and causes worst-case latency to exceed the real-time budget, that creates a concrete reason to investigate optimisation.

The progression might then move from ordinary Python improvements to more specialised implementations, potentially including compiled or lower-level code where the measurements justify it.

The important principle is that **the benchmark should motivate the optimisation**.

---

## 6. Separate the Real-Time Path from Everything Else

Another architectural goal for v2 is to distinguish work that must happen within the real-time budget from work that does not.

```text
Audio input
    │
    ▼
Real-time processing
    │
 < 46.44 ms
    │
    ┌──────────┴──────────┐
    ▼                     ▼
Live feedback          Event stream
                            │
                            ▼
                    Offline / async work
                            │
                    ┌───────┴───────┐
                    ▼               ▼
                Alignment        Scoring
```

Live feedback needs predictable latency.

A more computationally expensive analysis of the completed performance does not necessarily need to compete for the same real-time processing budget.

This separation should allow v2 to improve both performance and architectural clarity without prematurely forcing every part of the system into the same execution model.

---

## 7. Developer Velocity vs Performance

One of the things I want v2 to explore deliberately is the trade-off between **developer velocity and extreme performance**.

A highly optimised implementation is not automatically a better implementation.

For some parts of the application, a clear Python implementation may be preferable because the computational cost is insignificant relative to the real-time budget.

For a genuine hot path, however, a more specialised implementation may be justified.

Rather than maintaining two competing production implementations purely for the sake of having two implementations, I want to use **small, measurable experiments and benchmarked alternatives** where the trade-off is educational or technically significant.

This also provides useful historical context for future changes.

For example, if a future pitch detector increases latency beyond the real-time budget, the project should make it possible to answer:

1. Where did the additional latency come from?
2. Which stage became the bottleneck?
3. What optimisation was attempted?
4. What did it improve?
5. What did it cost in complexity or memory?
6. Did the final implementation actually satisfy the real-time constraint?

The goal is therefore not simply:

> **"Make the program as fast as possible."**

It is:

> **"Make the program useful, make the architecture right, identify the actual constraints, and then optimise against those constraints."**

---

## 8. Architectural Friction That Shaped the Chinese App

The problems encountered in v1 directly influenced the design of the Chinese Vocabulary Training platform.

| Friction in Violin v1                                           | Response in Chinese App / Violin v2                                   |
| --------------------------------------------------------------- | --------------------------------------------------------------------- |
| Business logic mixed with audio callbacks                       | Domain logic separated from infrastructure through ports and adapters |
| Global state and circular imports                               | Explicit dependency injection and composition-root wiring             |
| Tests retrofitted around existing implementation                | Tests designed around isolated domain behaviour                       |
| Observability added late                                        | Telemetry and structured logging treated as architectural concerns    |
| Naïve benchmarking that could not confidently support decisions | Controlled performance harnesses and statistical thinking             |
| Hard-coded pieces and in-memory assumptions                     | Persistent, queryable domain models                                   |
| Infrastructure details leaking into core logic                  | Explicit boundaries between domain and infrastructure                 |
| Difficult-to-change architecture                                | Smaller components with explicit contracts                            |

The Chinese application therefore wasn’t simply a separate project.

It was, in part, an opportunity to take the problems discovered while building this application and learn how to avoid them.

v2 now provides an opportunity to bring those lessons back.

---

## 9. What I Am Taking Into v2

- Treat the product question “what should I practise next?” as a first-class design constraint.
- Make intermediate pipeline behaviour observable, not just the final score.
- Establish a clear real-time budget and optimise against **maximum** latency.
- Separate the real-time path from offline analysis.
- Prefer measurable experiments over premature optimisation.
- Keep developer velocity high for non-hot-path code.
- Bring the architectural discipline learned in the Chinese app back into this project.

---

_This document will be updated as v2 progresses and new lessons emerge._
