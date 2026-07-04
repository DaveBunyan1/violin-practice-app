# Telemetry & Performance Benchmarking Specification (v1.8.2)

This document establishes the architecture, metrics, and implementation rules for the telemetry framework introduced in **v1.8.2**. The explicit purpose of this layer is to establish an empirical performance baseline for the application's real-time digital signal processing (DSP) operations, ensuring that subsequent architectural refactors in **v1.9.0** can be rigorously evaluated against objective data.

---

## 1. Core Architectural Strategy

Real-time audio processing operates under strict temporal constraints. For a standard buffer size ($N = 2048$ samples) sampled at $44.1\text{ kHz}$, the processing window for an entire frame is exactly:

$$\Delta t = \frac{2048}{44100} \approx 46.44\text{ ms}$$

If the combined execution time of the pitch detection algorithm, state updates, and rendering logic exceeds $\Delta t$, an **audio buffer underrun (dropout)** occurs, causing audible glitches and compromised accuracy.

To prevent the monitoring system from causing the very latency it is designed to measure, the telemetry layer adheres to three strict constraints:

1. **Zero Allocations in the Audio Thread:** No memory allocations (e.g., creating objects, expanding arrays) are permitted inside the callback loop to eliminate Garbage Collection (GC) pauses.
2. **Asynchronous Reporting:** Metrics are written to a fixed-size, pre-allocated ring buffer or typed arrays and drained asynchronously to a background worker or low-priority thread for logging.
3. **High-Resolution Timing:** Monotonic, high-resolution clocks are used (`performance.now()` in JS/TS, `mach_absolute_time()` in Apple environments, or `clock_gettime(CLOCK_MONOTONIC)` in C++) to guarantee sub-millisecond precision.

---

## 2. Key Performance Indicators (KPIs)

The telemetry layer monitors four distinct vectors to assess app performance:

### A. Digital Signal Processing (DSP) Latency

- **Definition:** The precise wall-clock duration taken by the pitch detection algorithm (Autocorrelation in v1.8.x) to process a single audio frame.
- **Target:** $< 10\\text{ ms}$ average processing time per frame (leaving remaining time for system overhead and UI rendering).

### B. Frame Compute Margin

- **Definition:** The percentage of the available processing window remaining after processing a frame.
- **Formula:** $$\\text{Margin (\\%)} = \\left(1 - \\frac{\\text{DSP Latency}}{\\Delta t}\\right) \\times 100$$
- **Target:** $> 75\\%$ headroom under typical playing conditions.

### C. Jitter & Deadline Excursion Count

- **Definition:** Jitter measures the statistical variance in frame processing intervals. An _Excursion_ is recorded every time the processing time crosses the $46.44\\text{ ms}$ threshold ($\\text{Margin} \\le 0\\%$).
- **Target:** $0$ Excursions per 5-minute practice block; Jitter Standard Deviation $\\sigma < 2\\text{ ms}$.

### D. Memory Footprint Stability (GC Pressure)

- **Definition:** Heap expansion and the frequency/duration of GC pauses during an active audio streaming session.
- **Target:** Stable baseline heap with horizontal plateau; zero micro-stutters during pitch analysis.

---

## 3. Data Collection Architecture

[ Audio Hardware / Input Stream ]
│
▼ (Triggers Audio Callback Loop)
┌────────────────────────────────────────────────────────┐
│ AUDIO PROCESSING THREAD (Time-Critical) │
│ │
│ t0 = high_res_clock() │
│ [ Execute Autocorrelation Algorithm ] │
│ t1 = high_res_clock() │
│ │
│ dsp_latency = t1 - t0 │
│ WriteMetricsToRingBuffer(dsp_latency) ──┐ │
└──────────────────────────────────────────│─────────────┘
│ (Lock-free write)
▼
┌────────────────────────────────────────────────────────┐
│ SHARED LOCK-FREE RING BUFFER │
│ [ Pre-allocated Array / SharedArrayBuffer ] │
└──────────────────────────────────────────┬─────────────┘
│ (Asynchronous poll)
▼
┌────────────────────────────────────────────────────────┐
│ BACKGROUND / MAIN THREAD (Low-Priority) │
│ │
│ ReadMetricsFromRingBuffer() │
│ Aggregate Statistics (Mean, P95, P99, Excursions) │
│ Write to Benchmarking Log File │
└────────────────────────────────────────────────────────┘

---

## 4. Benchmark Log Schema (v1.8.2 Output Format)

Telemetry logs are exported as a structured JSON array or CSV containing flat metrics blocks aggregated over a 10-second window, or captured per individual frame during explicit continuous stress-testing profiles.

```json
{
  "telemetry_version": "1.8.2",
  "app_version": "1.8.2",
  "environment": {
    "sample_rate_hz": 44100,
    "buffer_size_samples": 2048,
    "allocated_frame_window_ms": 46.439,
    "audio_backend": "CoreAudio"
  },
  "metrics_summary": {
    "session_duration_seconds": 600.0,
    "total_frames_processed": 12920,
    "dsp_latency_stats_ms": {
      "mean": 6.42,
      "median": 5.8,
      "p95": 11.2,
      "p99": 24.5,
      "max": 48.12
    },
    "frame_compute_margin_pct": {
      "mean": 86.17,
      "min": -3.62
    },
    "deadline_excursions": {
      "count": 3,
      "percentage": 0.023
    },
    "jitter_sigma_ms": 1.45,
    "memory_delta_mb": 4.2
  }
}
```

---

## 5. Protocol for Incremental Integration & Verification (v1.9.0 Pipeline)

To safely isolate and validate individual v1.9.0 optimizations, developers must execute the following sequence:

1. **Establish Control (v1.8.2 Baseline):** Run a standardized audio playback file (a pre-recorded scale or exercise wave file to remove physical performance variance) and record telemetry log data.
2. **Apply Single Variant (v1.9.x component):** Merge exactly one backend modification (e.g., moving processing to a Worker thread, or refactoring the state manager update logic).
3. **Execute Test Profile:** Run the identical audio playback file under identical load parameters.
4. **Evaluate Metrics Delta:** Compare the P95 latency, excursion counts, and heap stability against the control baseline.

- **Pass Criteria:** Any modification must result in a $\Delta \le 0$ for Excursion Count, and equal or lower P95/P99 latency bounds.
- **Fail/Rollback Criteria:** Any increase in frame deadline excursions or a degradation of mean Compute Margin below target thresholds dictates immediate rejection of the branch.

# Review/draft parts

**Telemetry Specification ratified for v1.8.2 rollout. Refer to ALGORITHMS.md for specific computation profiles of the Autocorrelation routine.**

"Context Propagation Strategy: To ensure a strict Separation of Concerns (SoC), telemetry trace metadata is passed explicitly down the call stack via parameter-passing rather than mutating the core event payloads. This ensures zero data pollution on client-bound WebSockets and allows the performance monitoring layer to be compiled out or disabled seamlessly in production environments."
