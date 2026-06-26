"use client";

import { useEffect, useState, useRef } from "react";
import ControlDeck from "./components/ControlDeck";
import TimelineCanvas from "./components/TimelineCanvas";
import PerformanceAnalytics from "./components/PerformanceAnalytics";

type TargetNote = { note: string; time: number; duration: number };
type ActivePiece = {
  id: number;
  title: string;
  total_duration: number;
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
    try {
      const res = await fetch(`${API_BASE}/session/start`, { method: "POST" });
      if (!res.ok) return;
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
        maxWidth: 900,
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

      {piece && (
        <TimelineCanvas
          notes={piece.notes}
          totalDuration={piece.total_duration}
          elapsedTime={elapsedTime}
          isSessionActive={isSessionActive}
        />
      )}

      <PerformanceAnalytics report={sessionReport} />
    </div>
  );
}
