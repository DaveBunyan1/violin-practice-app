"use client";

import NoteBlock from "../notes/NoteBlock";
import { MusicalNote } from "@/app/types/Note";

interface BarContainerProps {
  barNumber: number;
  timeSignatureNumerator: number; // e.g., 3 for 3/4, 4 for 4/4
  notes: MusicalNote[];
}

export default function BarContainer({
  barNumber,
  timeSignatureNumerator,
  notes,
}: BarContainerProps) {
  const baseWidthPerBeat = 75; // Matches the width unit inside NoteBlock
  const barWidth = timeSignatureNumerator * baseWidthPerBeat;

  return (
    <div
      style={{
        width: `${barWidth}px`,
        backgroundColor: "#16161a",
        border: "1px solid #232329",
        borderRadius: "8px",
        padding: "0px",
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        boxSizing: "border-box",
        flexShrink: 0, // Prevents layout wrappers from crushing the bar width
      }}
    >
      {/* Bar Heading */}
      <div
        style={{
          color: "#dddddd",
          fontSize: "13px",
          fontWeight: "600",
          userSelect: "none",
        }}
      >
        Bar {barNumber}
      </div>

      {/* Beat Indicators Grid (1, 2, 3...) */}
      <div
        style={{
          display: "flex",
          width: "100%",
          boxSizing: "border-box",
        }}
      >
        {Array.from({ length: timeSignatureNumerator }).map((_, beatIdx) => (
          <span
            key={beatIdx}
            style={{
              width: `${baseWidthPerBeat}px`,
              color: "#dddddd",
              fontSize: "11px",
              textAlign: "center",
              fontWeight: "500",
              userSelect: "none",
            }}
          >
            {beatIdx + 1}
          </span>
        ))}
      </div>

      {/* Notes Stream Box */}
      <div
        style={{
          display: "flex",
          width: "100%",
          height: "50px", // Matches NoteBlock height
          borderRadius: "6px",
          overflow: "hidden", // Clean clip for the internal flush notes
          backgroundColor: "#20262E", // Base empty rest backing tracking
        }}
      >
        {notes.map((note, index) => (
          <NoteBlock
            key={index}
            pitch={note.pitch}
            value={note.value}
            isRest={note.isRest}
          />
        ))}
      </div>
    </div>
  );
}
