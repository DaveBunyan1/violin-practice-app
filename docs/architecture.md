                ┌──────────────────────────┐

Microphone ───► │ PitchObservationEvent │
└─────────────┬────────────┘
▼
NoteSegmenter (stateful)
│
┌───────────────────┴───────────────────┐
▼ ▼
Live path (real-time) Session path (batch)
▼ ▼
LiveDashboardMetrics PerformedNoteEvent
▼ ▼
WebSocket UI SessionController storage
▼
Alignment + Scoring Engine
▼
ScoreResult (end)
