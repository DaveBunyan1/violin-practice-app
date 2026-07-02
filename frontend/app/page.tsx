"use client";

import { useEffect, useState, useRef } from "react";
import ControlDeck from "./components/ControlDeck";
import TimelineCanvas from "./components/practice/TimelineCanvas";
import PerformanceAnalytics from "./components/practice/PerformanceAnalytics";

type TargetNote = { note: string; time: number; duration: number };
type ActivePiece = {
  id: number;
  title: string;
  total_duration: number;
  bpm: number;
  time_signature_numerator: number;
  notes: TargetNote[];
};

const API_BASE = `http://${process.env.NEXT_PUBLIC_WEBSOCKET_HOST || "localhost"}:${process.env.NEXT_PUBLIC_WEBSOCKET_PORT || "8000"}`;

export default function Page() {
  const [connected, setConnected] = useState<boolean>(false);
  const [isSessionActive, setIsSessionActive] = useState<boolean>(false);
  const [piece, setPiece] = useState<ActivePiece | null>(null);
  const [sessionReport, setSessionReport] = useState<any | null>(null);
  const [elapsedTime, setElapsedTime] = useState<number>(0);

  const animationRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);

  // WebSocket Live Loop Link
  useEffect(() => {
    const socket = new WebSocket(
      `ws://${process.env.NEXT_PUBLIC_WEBSOCKET_HOST || "localhost"}:${process.env.NEXT_PUBLIC_WEBSOCKET_PORT || "8000"}/stream`,
    );
    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    return () => socket.close();
  }, []);

  // Fetch Piece Blueprint Data
  useEffect(() => {
    async function loadPiece() {
      try {
        const res = await fetch(`${API_BASE}/repertoire/active`);
        if (res.ok) setPiece(await res.json());
      } catch (err) {
        console.error("Failed to load active piece blueprint:", err);
      }
    }
    loadPiece();
  }, []);

  const updateTimelineCursor = (timestamp: number) => {
    if (!startTimeRef.current || !piece) return;
    const elapsed = (timestamp - startTimeRef.current) / 1000;
    if (elapsed >= piece.total_duration) {
      handleEndSession();
    } else {
      setElapsedTime(elapsed);
      animationRef.current = requestAnimationFrame(updateTimelineCursor);
    }
  };

  const handleStartSession = async () => {
    if (!piece) return; // Guard clause to ensure blueprint data is loaded

    try {
      // 1. Calculate approximate total bars to pass as a fallback end_bar
      const beatDuration = 60 / (piece.bpm || 116);
      const barDuration = beatDuration * (piece.time_signature_numerator || 4);
      const totalBars = Math.ceil(piece.total_duration / barDuration) || 17;

      // 2. Fire the POST request with the required payload body
      const res = await fetch(`${API_BASE}/session/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          piece_id: piece.id,
          start_bar: null,
          end_bar: null,
        }),
      });

      if (!res.ok) {
        // Log explicit error payload if the backend rejects it for other reasons (e.g., status 400)
        const errData = await res.json();
        console.error("Session reject reason:", errData);
        return;
      }

      setSessionReport(null);
      setIsSessionActive(true);
      setElapsedTime(0);
      startTimeRef.current = performance.now();
      animationRef.current = requestAnimationFrame(updateTimelineCursor);
    } catch (err) {
      console.error("Failed to start session:", err);
    }
  };
  const handleEndSession = async () => {
    try {
      const res = await fetch(`${API_BASE}/session/end`, { method: "POST" });
      setIsSessionActive(false);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      if (res.ok) setSessionReport(await res.json());
    } catch (err) {
      console.error("Failed to safely close performance window:", err);
    }
  };

  return (
    <div
      style={{
        padding: 40,
        fontFamily: "sans-serif",
        maxWidth: 1500,
        margin: "0 auto",
        backgroundColor: "#121212",
        color: "#e0e0e0",
        minHeight: "100vh",
      }}
    >
      <h2>🎻 Practice Timeline Monitor v1.7.0</h2>
      <p>Connection: {connected ? "🟢 Linked" : "🔴 Offline"}</p>

      {piece && (
        <div style={{ marginBottom: 20 }}>
          <h3 style={{ color: "#BB86FC", margin: "5px 0" }}>
            Piece: {piece.title}
          </h3>
          <p style={{ fontSize: 14, color: "#aaa" }}>
            BPM: {piece.bpm || 116} | Time Signature:{" "}
            {piece.time_signature_numerator || 4}/4
          </p>
          <p style={{ fontSize: 14, color: "#aaa" }}>
            Duration: {piece.total_duration.toFixed(1)}s | Position:{" "}
            {elapsedTime.toFixed(2)}s
          </p>
        </div>
      )}

      <ControlDeck
        isSessionActive={isSessionActive}
        onStart={handleStartSession}
        onEnd={handleEndSession}
      />

      {piece &&
        (() => {
          // 1. Core time math for calculations
          const currentBpm = piece.bpm || 116;
          const timeSigNumerator = piece.time_signature_numerator || 4;
          const beatDuration = 60 / currentBpm;
          const barDuration = beatDuration * timeSigNumerator;

          // 2. Determine how many total bars exist in this piece
          const maxNoteTime = piece.notes.reduce(
            (max, n) => Math.max(max, n.time + n.duration),
            0,
          );
          const totalBarsCount = Math.max(
            1,
            Math.ceil(maxNoteTime / barDuration),
          );

          // 3. Map flat absolute-timed notes into our clean, sequential Bar structure
          const structuredBars = Array.from({ length: totalBarsCount }).map(
            (_, barIdx) => {
              const barStartTime = barIdx * barDuration;

              // We are going to build this bar beat-by-beat sequentially
              const notesForBar: any[] = [];

              for (let beatIdx = 0; beatIdx < timeSigNumerator; beatIdx++) {
                const absoluteBeatTime = barStartTime + beatIdx * beatDuration;
                const errorMargin = 0.05;

                // Find if a note from the backend starts on this specific beat
                const matchingNote = piece.notes.find(
                  (n) => Math.abs(n.time - absoluteBeatTime) < errorMargin,
                );

                if (matchingNote) {
                  // Determine structural NoteValue string based on note duration
                  let val:
                    | "whole"
                    | "half"
                    | "quarter"
                    | "eighth"
                    | "sixteenth" = "quarter";

                  if (
                    Math.abs(matchingNote.duration - beatDuration * 4) <
                    errorMargin
                  )
                    val = "whole";
                  else if (
                    Math.abs(matchingNote.duration - beatDuration * 2) <
                    errorMargin
                  )
                    val = "half";
                  else if (
                    Math.abs(matchingNote.duration - beatDuration) < errorMargin
                  )
                    val = "quarter";
                  else if (
                    Math.abs(matchingNote.duration - beatDuration * 0.5) <
                    errorMargin
                  )
                    val = "eighth";
                  else if (
                    Math.abs(matchingNote.duration - beatDuration * 0.25) <
                    errorMargin
                  )
                    val = "sixteenth";

                  notesForBar.push({
                    pitch: matchingNote.note,
                    value: val,
                    isRest: false,
                  });

                  // If the note spans multiple beats (like a half or whole note),
                  // fast-forward the loop counter past the beats it covers
                  const extraBeatsToSkip =
                    Math.round(matchingNote.duration / beatDuration) - 1;
                  beatIdx += Math.max(0, extraBeatsToSkip);
                } else {
                  // No note starts on this beat -> Drop a proper 1-beat quarter rest placeholder!
                  notesForBar.push({
                    pitch: "",
                    value: "quarter",
                    isRest: true,
                  });
                }
              }

              return {
                barNumber: barIdx + 1,
                notes: notesForBar,
              };
            },
          );

          return (
            <TimelineCanvas
              bars={structuredBars} // Passing the brand new structured array
              bpm={currentBpm}
              timeSignatureNumerator={timeSigNumerator}
              elapsedTime={elapsedTime}
              isSessionActive={isSessionActive}
            />
          );
        })()}

      <PerformanceAnalytics report={sessionReport} />
    </div>
  );
}
