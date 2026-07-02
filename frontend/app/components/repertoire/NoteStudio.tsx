import React, { useState, useEffect } from "react";

interface NoteIn {
  note: string;
  time: number;
  duration: number;
}

interface Piece {
  id: number;
  title: string;
  bpm: number;
  time_signature_numerator: number;
  notes?: NoteIn[]; // 👈 Ensure your frontend type accounts for the relationship
}

interface NoteStudioProps {
  selectedPiece: Piece;
  onSaveNotes: (notes: NoteIn[]) => Promise<void>;
}

const VIOLIN_NOTE_POOL = [
  "G3",
  "G#3",
  "Ab3",
  "A3",
  "A#3",
  "Bb3",
  "B3",
  "C4",
  "C#4",
  "Db4",
  "D4",
  "D#4",
  "Eb4",
  "E4",
  "F4",
  "F#4",
  "Gb4",
  "G4",
  "G#4",
  "Ab4",
  "A4",
  "A#4",
  "Bb4",
  "B4",
  "C5",
  "C#5",
  "Db5",
  "D5",
  "D#5",
  "Eb5",
  "E5",
  "F5",
  "F#5",
  "Gb5",
  "G5",
  "G#5",
  "Ab5",
  "A5",
  "A#5",
  "Bb5",
  "B5",
  "C6",
  "C#6",
  "Db6",
  "D6",
  "D#6",
  "Eb6",
  "E6",
  "F6",
  "F#6",
  "Gb6",
  "G6",
  "G#6",
  "Ab6",
  "A6",
  "A#6",
  "Bb6",
  "B6",
  "C7",
  "C#7",
  "Db7",
  "D7",
  "D#7",
  "Eb7",
  "E7",
];

export const NoteStudio: React.FC<NoteStudioProps> = ({
  selectedPiece,
  onSaveNotes,
}) => {
  const [notesList, setNotesList] = useState<NoteIn[]>([]);
  const [selectedNote, setSelectedNote] = useState<string>("G4");
  const [targetBeat, setTargetBeat] = useState<number>(0);
  const [noteDurationBeats, setNoteDurationBeats] = useState<number>(1);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const beatUnitSeconds = 60 / selectedPiece.bpm;

  // 🔄 Sync state whenever the user switches between different repertoire pieces
  useEffect(() => {
    if (selectedPiece.notes && selectedPiece.notes.length > 0) {
      // Pre-populate with existing notes sorted chronologically
      const sortedExisting = [...selectedPiece.notes].sort(
        (a, b) => a.time - b.time,
      );
      setNotesList(sortedExisting);

      // Smart positioning: set the next insertion beat right at the end of the current piece
      const lastNote = sortedExisting[sortedExisting.length - 1];
      const nextSuggestedBeat =
        (lastNote.time + lastNote.duration) / beatUnitSeconds;
      setTargetBeat(parseFloat(nextSuggestedBeat.toFixed(2)));
    } else {
      setNotesList([]);
      setTargetBeat(0);
    }
  }, [selectedPiece, beatUnitSeconds]);

  const handleAddNote = () => {
    const absoluteTime = targetBeat * beatUnitSeconds;
    const absoluteDuration = noteDurationBeats * beatUnitSeconds;

    const newNote: NoteIn = {
      note: selectedNote,
      time: absoluteTime,
      duration: absoluteDuration,
    };

    setNotesList((prev) => [...prev, newNote].sort((a, b) => a.time - b.time));
    setTargetBeat((prev) => parseFloat((prev + noteDurationBeats).toFixed(2)));
  };

  const handleRemoveNote = (indexToRemove: number) => {
    setNotesList((prev) => prev.filter((_, idx) => idx !== indexToRemove));
  };

  const handlePublish = async () => {
    setIsSubmitting(true);
    try {
      await onSaveNotes(notesList);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        background: "#222",
        padding: "24px",
        borderRadius: "8px",
        border: "1px solid #eaeaea",
      }}
    >
      <h3>🎼 Editing Pitch Layout: {selectedPiece.title}</h3>
      <p style={{ color: "#666", fontSize: "14px" }}>
        Grid Scale: <strong>{selectedPiece.bpm} BPM</strong> | 1 Beat ={" "}
        {beatUnitSeconds.toFixed(4)} seconds
      </p>

      {/* INPUT BUILDER BLOCK */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          background: "#222",
          padding: "16px",
          borderRadius: "6px",
          alignItems: "flex-end",
          margin: "16px 0",
          flexWrap: "wrap",
        }}
      >
        <div>
          <label
            style={{
              display: "block",
              fontSize: "12px",
              fontWeight: "bold",
              marginBottom: "4px",
            }}
          >
            Pitch Dropdown
          </label>
          <select
            value={selectedNote}
            onChange={(e) => setSelectedNote(e.target.value)}
            style={{
              padding: "8px",
              borderRadius: "4px",
              border: "1px solid #ccc",
            }}
          >
            {VIOLIN_NOTE_POOL.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            style={{
              display: "block",
              fontSize: "12px",
              fontWeight: "bold",
              marginBottom: "4px",
            }}
          >
            Beat Position
          </label>
          <input
            type="number"
            step="0.25"
            value={targetBeat}
            onChange={(e) => setTargetBeat(parseFloat(e.target.value) || 0)}
            style={{
              padding: "8px",
              width: "90px",
              borderRadius: "4px",
              border: "1px solid #ccc",
            }}
          />
        </div>

        <div>
          <label
            style={{
              display: "block",
              fontSize: "12px",
              fontWeight: "bold",
              marginBottom: "4px",
            }}
          >
            Duration (Beats)
          </label>
          <input
            type="number"
            step="0.25"
            value={noteDurationBeats}
            onChange={(e) =>
              setNoteDurationBeats(parseFloat(e.target.value) || 1)
            }
            style={{
              padding: "8px",
              width: "80px",
              borderRadius: "4px",
              border: "1px solid #ccc",
            }}
          />
        </div>

        <button
          onClick={handleAddNote}
          style={{
            padding: "9px 16px",
            background: "#0070f3",
            color: "#fff",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          + Add Note
        </button>
      </div>

      {/* RENDER GRID TABLE */}
      <div
        style={{
          maxHeight: "300px",
          overflowY: "auto",
          border: "1px solid #eaeaea",
          borderRadius: "6px",
        }}
      >
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: "14px",
          }}
        >
          <thead style={{ background: "#111", position: "sticky", top: 0 }}>
            <tr
              style={{ textAlign: "left", borderBottom: "1px solid #eaeaea" }}
            >
              <th style={{ padding: "10px" }}>Pitch</th>
              <th style={{ padding: "10px" }}>Beat Location</th>
              <th style={{ padding: "10px" }}>Backend Time Variables</th>
              <th style={{ padding: "10px", textAlign: "right" }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {notesList.length === 0 ? (
              <tr>
                <td
                  colSpan={4}
                  style={{
                    padding: "20px",
                    textAlign: "center",
                    color: "#999",
                  }}
                >
                  No sequence data mapped out yet.
                </td>
              </tr>
            ) : (
              notesList.map((note, idx) => (
                <tr key={idx} style={{ borderBottom: "1px solid #f9f9f9" }}>
                  <td style={{ padding: "10px", fontWeight: "bold" }}>
                    {note.note}
                  </td>
                  <td style={{ padding: "10px" }}>
                    Beat {(note.time / beatUnitSeconds).toFixed(2)} (
                    {(note.duration / beatUnitSeconds).toFixed(2)} b)
                  </td>
                  <td
                    style={{
                      padding: "10px",
                      fontFamily: "monospace",
                      fontSize: "12px",
                      color: "#555",
                    }}
                  >
                    t: {note.time.toFixed(3)}s | d: {note.duration.toFixed(3)}s
                  </td>
                  <td style={{ padding: "10px", textAlign: "right" }}>
                    <button
                      onClick={() => handleRemoveNote(idx)}
                      style={{
                        color: "red",
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                      }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: "20px", textAlign: "right" }}>
        <button
          onClick={handlePublish}
          disabled={isSubmitting || notesList.length === 0}
          style={{
            padding: "12px 20px",
            background: "#10b981",
            color: "#fff",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            fontWeight: "bold",
            opacity: isSubmitting ? 0.6 : 1,
          }}
        >
          {isSubmitting
            ? "Syncing Matrix..."
            : "💾 Save & Recompute Track Duration"}
        </button>
      </div>
    </div>
  );
};
