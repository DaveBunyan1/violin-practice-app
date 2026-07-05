My backend code was suitable for use in v1.2.0, after cents error was added. Between there and v1.8.0, I made changes to improve the rough backend that still existed since before v1.0.0, such as adding persistence, a way to add a piece to the repertoire, able to practice at different bpm and being able to practice full pieces vs specific bars of a piece, with basic analytics.

My thought for v1.9.0 was to completed refactor the backend, so I set up a small test suite in v1.8.1, and then as I was refactoring and changing a lot, I decided it was better to go back to v1.8.1 to set up telemetry to properly inform my architectural decisions. So after creating v1.8.2, and running a session for an hour with tv background noise for a benchmark, my first step for v1.9.0 was to implement a runtime graph. The global singletons had started to get out of hand, and then I was starting to run into circular imports when I tried to implement the telemetry.

I was using a 2048 buffer size for my excursion level (i.e. anything chunk taking longer than 46.44ms was bad), but after testing my v1.8.2 for an hour, and 20 minutes in to testing my v1.9.0, I realised my buffer size was actually 8192 from when I first started making the app.

I decided that the runtime graph was a necessity purely for develeper velocity, so I concluded to let this run for an hour at the same buffer size for a baseline. The benchmark results for both can be found in (Link?)docs/v1.8.2_baseline_metrics_1_hour.json and (Link?)v1.9.0_baseline_metrics_1_hour.json respectively, but to summarize, while the 3_process_note values drastically improved, and the total_pipeline_cycle values were also better, the most important stat revealed was that in v1.8.2, 4454 frames were captured, while in v1.9.0, only 2408 frames were captured.

So while it showed improvement across the board:
**v1.8.2:**

```json
      "total_pipeline_lifecycle": {
        "mean": 7.255,
        "std": 3.581,
        "p95": 14.301,
        "p99": 20.227,
        "max": 49.984
      }
```

**v1.9.0:**

```json
      "total_pipeline_lifecycle": {
        "mean": 6.211,
        "std": 3.131,
        "p95": 11.831,
        "p99": 17.226,
        "max": 26.992
      }
```
