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
        backgroundColor: "transparent", // Cleaned out card backing
        border: "none", // Stripped all native frame borders
        padding: "0px", // Flushed edge-to-edge
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        boxSizing: "border-box",
        flexShrink: 0,
      }}
    >
      {/* Bar Header */}
      <div
        style={{
          color: "#ddd",
          fontSize: "13px",
          fontWeight: "600",
          paddingLeft: "4px",
          userSelect: "none",
        }}
      >
        Bar {barNumber}
      </div>

      {/* Beat Indicators Grid */}
      <div style={{ display: "flex", width: "100%", boxSizing: "border-box" }}>
        {Array.from({ length: timeSignatureNumerator }).map((_, beatIdx) => (
          <span
            key={beatIdx}
            style={{
              width: `${baseWidthPerBeat}px`,
              color: "#ddd",
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
          height: "50px",
          borderRadius: "4px",
          overflow: "hidden",
          backgroundColor: "#20262E",
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
