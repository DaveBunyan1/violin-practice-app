"use client";

import RowContainer from "../music/rows/RowContainer";
import { MusicalNote } from "@/app/types/Note";

// Structuring our incoming structural dataset schema matching the backend pipeline
interface BarData {
  barNumber: number;
  notes: MusicalNote[];
}

interface TimelineCanvasProps {
  bars: BarData[];
  bpm: number;
  timeSignatureNumerator: number;
  elapsedTime: number;
  isSessionActive: boolean;
}

export default function TimelineCanvas({
  bars,
  bpm,
  timeSignatureNumerator,
  elapsedTime,
  isSessionActive,
}: TimelineCanvasProps) {
  // 1. Calculate how many bars fit on a single line row based on our target rule:
  //    4/4 -> 4 bars (16 beats)
  //    3/4 -> 5 bars (15 beats)
  //    2/4 -> 8 bars (16 beats)
  const barsPerLine = Math.floor(16 / timeSignatureNumerator);

  // 2. Determine how many total row lines are needed to display all bars
  const totalLines = Math.ceil(bars.length / barsPerLine);
  const linesArray = Array.from({ length: totalLines }, (_, i) => i);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
        backgroundColor: "#0d0d11", // Sleek dark slate back-panel background
        padding: "24px",
        borderRadius: "12px",
        border: "1px solid #1a1a24",
        boxSizing: "border-box",
        overflowX: "auto", // Gracefully handles horizontal scroll if screen real-estate gets tight
      }}
    >
      {/* Legend Header Panel */}
      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          gap: "20px",
          marginBottom: "24px",
          fontSize: "13px",
          color: "#888",
          userSelect: "none",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div
            style={{
              width: "12px",
              height: "12px",
              backgroundColor: "#3A1B79",
              borderRadius: "3px",
            }}
          />
          <span>Target Note</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div
            style={{
              width: "12px",
              height: "12px",
              backgroundColor: "#20252D",
              borderRadius: "3px",
            }}
          />
          <span>Rest / Empty Beat</span>
        </div>
      </div>

      {/* Sequential Rows Grid Stack */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          width: "100%",
        }}
      >
        {linesArray.map((lineIndex) => (
          <RowContainer
            key={lineIndex}
            lineIndex={lineIndex}
            timeSignatureNumerator={timeSignatureNumerator}
            bpm={bpm}
            bars={bars}
            elapsedTime={elapsedTime}
            isSessionActive={isSessionActive}
          />
        ))}
      </div>

      {/* Bottom Structural Piece Footprint Dashboard */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "32px",
          marginTop: "16px",
          paddingTop: "20px",
          borderTop: "1px solid #1a1a24",
          color: "#555964",
          fontSize: "12px",
          fontWeight: "600",
          letterSpacing: "0.5px",
          userSelect: "none",
        }}
      >
        <span>BPM: {bpm}</span>
        <span>TIME SIGNATURE: {timeSignatureNumerator}/4</span>
        <span>TOTAL BARS: {bars.length}</span>
      </div>
    </div>
  );
}
