"use client";

interface Props {
  startBar: number;
  endBar: number;
  setStartBar: (n: number) => void;
  setEndBar: (n: number) => void;
}

export default function PassageSelector({
  startBar,
  endBar,
  setStartBar,
  setEndBar,
}: Props) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 8,
        paddingLeft: 12,
        borderLeft: "2px solid #ccc",
      }}
    >
      <label style={{ fontWeight: "bold" }}>Passage Bounds:</label>

      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span>Bar</span>

        <input
          type="number"
          min={1}
          value={startBar}
          onChange={(e) => setStartBar(Math.max(1, Number(e.target.value)))}
          style={{ width: 60, padding: 4 }}
        />

        <span>to</span>

        <input
          type="number"
          min={startBar}
          value={endBar}
          onChange={(e) =>
            setEndBar(Math.max(startBar, Number(e.target.value)))
          }
          style={{ width: 60, padding: 4 }}
        />
      </div>
    </div>
  );
}
