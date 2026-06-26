"use client";

interface ControlDeckProps {
  isSessionActive: boolean;
  onStart: () => void;
  onEnd: () => void;
}

export default function ControlDeck({
  isSessionActive,
  onStart,
  onEnd,
}: ControlDeckProps) {
  return (
    <div style={{ display: "flex", gap: 10, marginBottom: 40 }}>
      <button
        onClick={onStart}
        disabled={isSessionActive}
        style={{
          padding: "12px 24px",
          cursor: isSessionActive ? "not-allowed" : "pointer",
          borderRadius: 4,
          border: "none",
          fontWeight: "bold",
        }}
      >
        ▶ Start Performance Run
      </button>
      <button
        onClick={onEnd}
        disabled={!isSessionActive}
        style={{
          padding: "12px 24px",
          backgroundColor: "#CF6679",
          color: "white",
          cursor: !isSessionActive ? "not-allowed" : "pointer",
          borderRadius: 4,
          border: "none",
          fontWeight: "bold",
        }}
      >
        ⏹ Stop & Evaluate
      </button>
    </div>
  );
}
