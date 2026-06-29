"use client";

type Mode = "full" | "passage";

interface Props {
  mode: Mode;
  setMode: (mode: Mode) => void;
}

export default function PracticeModeSelector({ mode, setMode }: Props) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <span style={{ fontWeight: "bold" }}>Mode:</span>

      <div style={{ display: "flex", gap: 16 }}>
        <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <input
            type="radio"
            checked={mode === "full"}
            onChange={() => setMode("full")}
          />
          Full Piece
        </label>

        <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <input
            type="radio"
            checked={mode === "passage"}
            onChange={() => setMode("passage")}
          />
          Passage
        </label>
      </div>
    </div>
  );
}
