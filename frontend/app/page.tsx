"use client";

import { useEffect, useState, useRef } from "react";

// --- Structural Types ---
type TargetNote = {
  note: string;
  time: number;
  duration: number;
};

type ActivePiece = {
  id: number;
  title: string;
  total_duration: number;
  notes: TargetNote[];
};

const WS_HOST = process.env.NEXT_PUBLIC_WEBSOCKET_HOST || "localhost";
const WS_PORT = process.env.NEXT_PUBLIC_WEBSOCKET_PORT || "8000";
const API_BASE = `http://${WS_HOST}:${WS_PORT}`;

export default function Page() {
  const [connected, setConnected] = useState<boolean>(false);
  const [isSessionActive, setIsSessionActive] = useState<boolean>(false);
  const [piece, setPiece] = useState<ActivePiece | null>(null);

  // High-frequency animation tracking state
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const animationRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);

  // 1. WebSocket Connection Setup (For live pitch visualization later)
  useEffect(() => {
    const socket = new WebSocket(`ws://${WS_HOST}:${WS_PORT}/stream`);
    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    return () => socket.close();
  }, []);

  // 2. Fetch Active Piece Blueprint Configuration on Mount
  useEffect(() => {
    async function loadPiece() {
      try {
        const res = await fetch(`${API_BASE}/repertoire/active`);
        if (res.ok) {
          const data = await res.json();
          setPiece(data);
        }
      } catch (err) {
        console.error("Failed to fetch active target piece:", err);
      }
    }
    loadPiece();
  }, []);

  // 3. High-Resolution Animation Tracking Loop
  const updateTimelineCursor = (timestamp: number) => {
    if (!startTimeRef.current || !piece) return;

    const elapsed = (timestamp - startTimeRef.current) / 1000; // Convert ms to seconds

    if (elapsed >= piece.total_duration) {
      // Automatically stop tracking when we reach the end boundary window
      handleEndSession();
    } else {
      setElapsedTime(elapsed);
      animationRef.current = requestAnimationFrame(updateTimelineCursor);
    }
  };

  const handleStartSession = async () => {
    try {
      const res = await fetch(`${API_BASE}/session/start`, { method: "POST" });
      if (!res.ok) return;

      setIsSessionActive(true);
      setElapsedTime(0);
      startTimeRef.current = performance.now();
      animationRef.current = requestAnimationFrame(updateTimelineCursor);
    } catch (err) {
      console.error("Failed to start rehearsal:", err);
    }
  };

  const handleEndSession = async () => {
    try {
      await fetch(`${API_BASE}/session/end`, { method: "POST" });
      setIsSessionActive(false);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    } catch (err) {
      console.error("Failed to stop rehearsal:", err);
    }
  };

  // Calculate moving bar percentage position
  const playbackPercentage = piece
    ? (elapsedTime / piece.total_duration) * 100
    : 0;

  return (
    <div
      style={{
        padding: 40,
        fontFamily: "sans-serif",
        maxWidth: 900,
        margin: "0 auto",
        backgroundColor: "#121212",
        color: "#e0e0e0",
        minHeight: "100vh",
      }}
    >
      <h2>🎻 Practice Timeline Monitor v1.6.0</h2>
      <p>Connection: {connected ? "🟢 Linked" : "🔴 Offline"}</p>

      {piece && (
        <div style={{ marginBottom: 20 }}>
          <h3 style={{ color: "#BB86FC", margin: "5px 0" }}>
            Piece: {piece.title}
          </h3>
          <p style={{ fontSize: 14, color: "#aaa" }}>
            Duration: {piece.total_duration.toFixed(1)}s | Position:{" "}
            {elapsedTime.toFixed(2)}s
          </p>
        </div>
      )}

      {/* Control Actions */}
      <div style={{ display: "flex", gap: 10, marginBottom: 40 }}>
        <button
          onClick={handleStartSession}
          disabled={isSessionActive}
          style={{
            padding: "12px 24px",
            cursor: "pointer",
            borderRadius: 4,
            border: "none",
            fontWeight: "bold",
          }}
        >
          ▶ Start Performance Run
        </button>
        <button
          onClick={handleEndSession}
          disabled={!isSessionActive}
          style={{
            padding: "12px 24px",
            backgroundColor: "#CF6679",
            color: "white",
            cursor: "pointer",
            borderRadius: 4,
            border: "none",
            fontWeight: "bold",
          }}
        >
          ⏹ Stop & Evaluate
        </button>
      </div>

      {/* --- REPERTOIRE NOTATION TIMELINE VISUALIZER --- */}
      {piece && (
        <div
          style={{
            position: "relative",
            width: "100%",
            height: "200px",
            backgroundColor: "#1e1e1e",
            borderRadius: 8,
            border: "1px solid #333",
            overflow: "hidden",
            marginTop: 20,
          }}
        >
          {/* Dynamic Render Note Row Matrix */}
          {piece.notes.map((note, index) => {
            // Compute percentage width and left coordinates dynamically
            const leftPercent = (note.time / piece.total_duration) * 100;
            const widthPercent = (note.duration / piece.total_duration) * 100;

            return (
              <div
                key={index}
                style={{
                  position: "absolute",
                  left: `${leftPercent}%`,
                  width: `${widthPercent}%`,
                  top: "35%",
                  height: "50px",
                  backgroundColor: "#3700B3",
                  border: "2px solid #BB86FC",
                  borderRadius: 6,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 14,
                  fontWeight: "bold",
                  color: "#fff",
                  boxSizing: "border-box",
                }}
              >
                {note.note}
              </div>
            );
          })}

          {/* Smooth Moving Playback Timeline Bar */}
          <div
            style={{
              position: "absolute",
              left: `${playbackPercentage}%`,
              top: 0,
              width: "3px",
              height: "100%",
              backgroundColor: "#03DAC6",
              boxShadow: "0 0 10px #03DAC6",
              transition: isSessionActive ? "none" : "left 0.1s linear",
              zIndex: 10,
            }}
          />
        </div>
      )}
    </div>
  );
}
