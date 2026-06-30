"use client";

import { NoteValue, BEAT_VALUES } from "@/app/types/Note";

interface NoteBlockProps {
  pitch: string;
  value: NoteValue;
  isRest?: boolean;
}

export default function NoteBlock({
  pitch,
  value,
  isRest = false,
}: NoteBlockProps) {
  const beatValue = BEAT_VALUES[value];

  // Define our explicit dimensions
  const height = 50;
  const baseWidthPerBeat = 75;

  return (
    <div
      style={{
        // Proportional sizing based on the beat value
        width: `${beatValue * baseWidthPerBeat}px`,
        height: `${height}px`,

        backgroundColor: isRest ? "#20252D" : "#3A1B79",
        borderRight: "1px solid #121214",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxSizing: "border-box",
        flexShrink: 0,
      }}
    >
      {!isRest && (
        <span
          style={{
            color: "#ffffff",
            fontSize: "12px",
            fontWeight: "bold",
            letterSpacing: "0.5px",
            userSelect: "none",
          }}
        >
          {pitch}
        </span>
      )}
    </div>
  );
}
