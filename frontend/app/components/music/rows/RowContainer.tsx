"use client";

import BarContainer from "../bars/BarContainer";
import { MusicalNote } from "@/app/types/Note";

// Explicitly mapping out a layout schema for individual bars
interface BarData {
  barNumber: number;
  notes: MusicalNote[];
}

interface RowContainerProps {
  lineIndex: number;
  timeSignatureNumerator: number;
  bpm: number;
  bars: BarData[];
  elapsedTime: number;
  isSessionActive: boolean;
}

export default function RowContainer({
  lineIndex,
  timeSignatureNumerator,
  bpm,
  bars,
  elapsedTime,
  isSessionActive,
}: RowContainerProps) {
  const baseWidthPerBeat = 75;
  const beatDuration = 60 / bpm;
  const barDuration = beatDuration * timeSignatureNumerator;

  // 1. Calculate dynamic bars per line based on your formula
  const barsPerLine = Math.floor(16 / timeSignatureNumerator);
  const lineDuration = barDuration * barsPerLine;

  const lineStartTime = lineIndex * lineDuration;
  const lineEndTime = lineStartTime + lineDuration;

  // 2. Extract only the subset of bars that belong on this specific row line
  const startBarIdx = lineIndex * barsPerLine;
  const lineBars = bars.slice(startBarIdx, startBarIdx + barsPerLine);

  // 3. Playback Cursor Math: Check if the cursor is moving across this row line
  const isCursorInLine =
    elapsedTime >= lineStartTime && elapsedTime < lineEndTime;

  // Total beats in this specific row (e.g., 16 for 4/4, 15 for 3/4)
  const totalBeatsInRow = barsPerLine * timeSignatureNumerator;
  const totalRowWidth = totalBeatsInRow * baseWidthPerBeat;

  // Calculate the cursor position as a percentage of the actual filled row width
  const cursorPercent = isCursorInLine
    ? ((elapsedTime - lineStartTime) / lineDuration) * 100
    : 0;

  // Render an empty component if there are no bars left to print on this line
  if (lineBars.length === 0) return null;

  return (
    <div
      style={{
        position: "relative", // Anchors our scanning timeline cursor line
        width: `${totalRowWidth}px`, // Collapses perfectly to match the exact beat footprint
        margin: "0 auto 24px auto", // Centers the rows cleanly on your sheet workspace
      }}
    >
      {/* Horizontal Flex Grid housing our calculated Bar Containers */}
      <div
        style={{
          display: "flex",

          width: "100%",
        }}
      >
        {lineBars.map((bar, offset) => (
          <BarContainer
            key={offset}
            barNumber={bar.barNumber}
            timeSignatureNumerator={timeSignatureNumerator}
            notes={bar.notes}
          />
        ))}
      </div>

      {/* Global Playback Tracking Cursor */}
      {isCursorInLine && (
        <>
          {/* Cursor Head Down-Arrow Indicator */}
          <div
            style={{
              position: "absolute",
              left: `calc(${cursorPercent}% - 6px)`,
              top: "-8px",
              width: "0px",
              height: "0px",
              borderLeft: "6px solid transparent",
              borderRight: "6px solid transparent",
              borderTop: "8px solid #03DAC6",
              zIndex: 11,
            }}
          />
          {/* Vertical Scanning Core Matrix Line */}
          <div
            style={{
              position: "absolute",
              left: `${cursorPercent}%`,
              top: 0,
              width: "2px",
              height: "100%",
              backgroundColor: "#03DAC6",
              boxShadow: "0 0 8px #03DAC6",
              // Instant tracking response if practicing live, otherwise standard interface easing interpolation
              transition: isSessionActive ? "none" : "left 0.1s linear",
              zIndex: 10,
              pointerEvents: "none",
            }}
          />
        </>
      )}
    </div>
  );
}
