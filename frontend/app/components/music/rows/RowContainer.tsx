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
        position: "relative",
        width: `${totalRowWidth + 32}px`,
        backgroundColor: "#16161a",
        border: "1px solid #232329",
        borderRadius: "10px",
        padding: "12px",
        margin: "0 auto 6px auto",
        boxSizing: "border-box",
      }}
    >
      {/* Horizontal Flex Grid housing our transparent Bar Containers */}
      <div
        style={{
          position: "relative",
          display: "flex",
          gap: "0px",
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

        {/* Placeholder for when switching to sheet music */}
        {lineBars.map((_, offset) => {
          // Skip drawing a line after the very last bar panel on this row line
          if (offset === lineBars.length - 1) return null;

          const currentBarWidth = timeSignatureNumerator * baseWidthPerBeat;
          const lineLeftPosition = (offset + 1) * currentBarWidth;
        })}
      </div>

      {/* Global Playback Tracking Cursor */}
      {isCursorInLine && (
        <>
          {/* Adjusted left mapping to account for the parent wrapper's 16px left padding */}
          <div
            style={{
              position: "absolute",
              left: `calc(16px + ${cursorPercent}% - 6px)`,
              top: "6px",
              width: "0px",
              height: "0px",
              borderLeft: "6px solid transparent",
              borderRight: "6px solid transparent",
              borderTop: "8px solid #03DAC6",
              zIndex: 11,
            }}
          />
          <div
            style={{
              position: "absolute",
              left: `calc(16px + ${cursorPercent}%)`,
              top: "16px",
              width: "2px",
              height: "calc(100% - 32px)", // Snaps the line precisely within the cushioned row padding frame
              backgroundColor: "#03DAC6",
              boxShadow: "0 0 8px #03DAC6",
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
