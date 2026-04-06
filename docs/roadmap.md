## Phase 1: Pitch Detection MVP

Goal:

Detect and display pitch in real time

Steps:

1. Audio Input
   Capture microphone input (Python)
   Stream chunks (e.g. 1024 samples)
2. Signal Processing
   Normalize signal
   Apply window function (Hann)
3. Pitch Detection
   Implement autocorrelation
   Extract fundamental frequency
4. Note Mapping
   Convert frequency → note name
   Add cents deviation
5. Output
   Print to console
   Then send via WebSocket

---

## Phase 2: Frontend Visualization

Goal:

Live pitch display in browser

Steps:
Create Next.js app
Connect WebSocket
Display:
Note (A4, G3)
Frequency
Accuracy meter

---

## Phase 3: Metronome

Steps:
Implement BPM control
Audio click (Web Audio API)
Visual pulse

---

## Phase 4: Note Matching

Steps:
Define expected note sequence
Compare detected vs expected
Show correctness

---

## Phase 5: Sheet Music (later)

Steps:
Load MusicXML
Render notation
Sync with playback
