"use client";

import { Piece } from "../../types/Piece";
import TimelineCanvas from "@/app/components/practice/TimelineCanvas";

interface ActiveSessionCanvasProps {
  selectedPiece: Piece;
  elapsedTime: number;
  isActive: boolean;
  practiceBpm: number;
  config: {
    mode: "full" | "passage";
    startBar?: number;
    endBar?: number;
  };
  onEndSession: () => void;
}

function structureNotesIntoBars(piece: Piece, targetBpm: number, config: any) {
  const originalBpm = piece.bpm || 116; // TODO: Fix the piece.bpm missing and defaulting to 116
  const currentBpm = targetBpm || originalBpm;
  const timeSigNumerator = piece.time_signature_numerator || 4;
  const tempoScaleFactor = originalBpm / currentBpm;

  const beatDuration = 60 / currentBpm;
  const barDuration = beatDuration * timeSigNumerator;

  const scaledNotes =
    piece.notes?.map((n) => ({
      ...n,
      time: n.time * tempoScaleFactor,
      duration: n.duration * tempoScaleFactor,
    })) || [];

  const maxNoteTime = scaledNotes.reduce(
    (max, n) => Math.max(max, n.time + n.duration),
    0,
  );
  const totalBarsCount = Math.max(1, Math.ceil(maxNoteTime / barDuration));

  const allBars = Array.from({ length: totalBarsCount }).map((_, barIdx) => {
    const barStartTime = barIdx * barDuration;
    const notesForBar: any[] = [];

    for (let beatIdx = 0; beatIdx < timeSigNumerator; beatIdx++) {
      const absoluteBeatTime = barStartTime + beatIdx * beatDuration;
      const errorMargin = 0.05;

      const matchingNote = scaledNotes.find(
        (n) => Math.abs(n.time - absoluteBeatTime) < errorMargin,
      );

      if (matchingNote) {
        let val: "whole" | "half" | "quarter" | "eighth" | "sixteenth" =
          "quarter";
        if (Math.abs(matchingNote.duration - beatDuration * 4) < errorMargin)
          val = "whole";
        else if (
          Math.abs(matchingNote.duration - beatDuration * 2) < errorMargin
        )
          val = "half";
        else if (Math.abs(matchingNote.duration - beatDuration) < errorMargin)
          val = "quarter";
        else if (
          Math.abs(matchingNote.duration - beatDuration * 0.5) < errorMargin
        )
          val = "eighth";
        else if (
          Math.abs(matchingNote.duration - beatDuration * 0.25) < errorMargin
        )
          val = "sixteenth";

        notesForBar.push({
          pitch: matchingNote.note,
          value: val,
          isRest: false,
        });
        const extraBeatsToSkip =
          Math.round(matchingNote.duration / beatDuration) - 1;
        beatIdx += Math.max(0, extraBeatsToSkip);
      } else {
        notesForBar.push({ pitch: "", value: "quarter", isRest: true });
      }
    }

    return { barNumber: barIdx + 1, notes: notesForBar };
  });

  let renderedBars = allBars;
  let adjustedTotalDuration = (piece.total_duration || 60) * tempoScaleFactor;

  if (config.mode === "passage" && config.startBar && config.endBar) {
    const start = Number(config.startBar);
    const end = Number(config.endBar);

    // Slice only the bars within your target window bounds
    renderedBars = allBars.filter(
      (b) => b.barNumber >= start && b.barNumber <= end,
    );

    // Calculate duration strictly for the length of this passage snippet
    const totalPassageBars = end - start + 1;
    adjustedTotalDuration = totalPassageBars * barDuration;
  }

  return {
    bars: renderedBars,
    currentBpm,
    timeSigNumerator,
    adjustedTotalDuration,
  };
}

export default function ActiveSessionCanvas({
  selectedPiece,
  elapsedTime,
  isActive,
  practiceBpm,
  config,
  onEndSession,
}: ActiveSessionCanvasProps) {
  const { bars, currentBpm, timeSigNumerator, adjustedTotalDuration } =
    structureNotesIntoBars(selectedPiece, practiceBpm, config);

  return (
    <div
      style={{ padding: 40, maxWidth: 1400, margin: "0 auto", width: "100%" }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 20,
        }}
      >
        <div>
          <h2 style={{ color: "#BB86FC", margin: 0 }}>
            Now Practicing: {selectedPiece.title}
          </h2>
          <p style={{ color: "#aaa", margin: "4px 0 0 0", fontSize: "14px" }}>
            Time: {elapsedTime.toFixed(2)}s / {adjustedTotalDuration.toFixed(1)}
            s
          </p>
        </div>
        <button
          onClick={onEndSession}
          style={{
            padding: "10px 20px",
            backgroundColor: "#CF6679",
            color: "#fff",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          Stop Session
        </button>
      </div>

      <TimelineCanvas
        bars={bars}
        bpm={currentBpm}
        timeSignatureNumerator={timeSigNumerator}
        elapsedTime={elapsedTime}
        isSessionActive={isActive}
      />
    </div>
  );
}
