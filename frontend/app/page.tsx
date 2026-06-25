"use client";

import { useEffect, useState } from "react";

// --- Structural TypeScript Interfaces ---

type PitchData = {
  frequency: number;
  note: string;
  time: number;
  expected_note?: string;
};

type ScoreResult = {
  total_score: number;
  pitch_accuracy: number;
  timing_accuracy: number;
  notes_hit: number;
  notes_total: number;
};

type HistoricalSession = {
  id: number;
  start_time: string;
  end_time: string | null;
  total_score: number;
  pitch_accuracy: number;
  timing_accuracy: number;
  notes_hit: number;
  notes_total: number;
};

// --- Configuration ---
const WS_HOST = process.env.NEXT_PUBLIC_WEBSOCKET_HOST || "127.0.0.1";
const WS_PORT = process.env.NEXT_PUBLIC_WEBSOCKET_PORT || "8000";
const API_BASE = `http://${WS_HOST}:${WS_PORT}`;

export default function Page() {
  const [connected, setConnected] = useState<boolean>(false);
  const [isSessionActive, setIsSessionActive] = useState<boolean>(false);
  const [latestPitch, setLatestPitch] = useState<PitchData | null>(null);
  const [currentScore, setCurrentScore] = useState<ScoreResult | null>(null);
  const [history, setHistory] = useState<HistoricalSession[]>([]);

  // 1. WebSocket Lifecycle Management (Live Pitch Stream Only)
  useEffect(() => {
    const socket = new WebSocket(`ws://${WS_HOST}:${WS_PORT}/stream`);

    socket.onopen = () => {
      console.log("WebSocket stream established.");
      setConnected(true);
    };

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "pitch") {
        setLatestPitch(msg.data);
      }
    };

    socket.onclose = () => {
      console.log("WebSocket stream closed.");
      setConnected(false);
    };

    return () => socket.close();
  }, []);

  // 2. Load historical sessions on mount
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/sessions?limit=5`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (err) {
      console.error("Failed to fetch session timeline history:", err);
    }
  };

  // 3. REST Action: Start a physical practice session
  const startSession = async () => {
    try {
      const res = await fetch(`${API_BASE}/session/start`, { method: "POST" });
      if (!res.ok) {
        const errorData = await res.json();
        alert(`Error: ${errorData.detail}`);
        return;
      }
      setIsSessionActive(true);
      setCurrentScore(null); // Clear previous visual score panel
    } catch (err) {
      console.error("Failed to start session:", err);
    }
  };

  // 4. REST Action: End session and capture database record context
  const endSession = async () => {
    try {
      const res = await fetch(`${API_BASE}/session/end`, { method: "POST" });
      if (!res.ok) {
        const errorData = await res.json();
        alert(`Error: ${errorData.detail}`);
        return;
      }

      const data = await res.json();
      setIsSessionActive(false);
      setCurrentScore(data.score_result);

      // Refresh timeline history automatically to reflect the newly persisted row
      fetchHistory();
    } catch (err) {
      console.error("Failed to terminate session safely:", err);
    }
  };

  return (
    <div
      style={{
        padding: 40,
        fontFamily: "sans-serif",
        maxWidth: 800,
        margin: "0 auto",
      }}
    >
      <h1>🎻 Violin Practice Pipeline Harness</h1>
      <p>
        Connection: {connected ? "🟢 WebSocket Connected" : "🔴 Disconnected"}
      </p>
      <p>
        Engine State:{" "}
        {isSessionActive ? "⏺ Active Recording Session" : "⏸ Idle"}
      </p>

      {/* Control Actions Panel */}
      <div style={{ marginTop: 20, display: "flex", gap: 10 }}>
        <button
          onClick={startSession}
          disabled={isSessionActive}
          style={{ padding: "10px 20px", fontSize: 16, cursor: "pointer" }}
        >
          ▶ Start Practice Run
        </button>
        <button
          onClick={endSession}
          disabled={!isSessionActive}
          style={{
            padding: "10px 20px",
            fontSize: 16,
            backgroundColor: "#f44336",
            color: "white",
            border: "none",
            cursor: "pointer",
          }}
        >
          ⏹ End Run
        </button>
      </div>

      {/* Live Stream Audio Analysis Dashboard */}
      <div
        style={{
          marginTop: 40,
          background: "#0c0c0c",
          padding: 20,
          borderRadius: 8,
        }}
      >
        <h3>Live Audio Tracking Context</h3>
        {latestPitch ? (
          <>
            <h2 style={{ fontSize: 64, margin: "10px 0" }}>
              {latestPitch.note}
            </h2>
            <p>Frequency: {latestPitch.frequency.toFixed(2)} Hz</p>
            <p>Relative Offset: {latestPitch.time.toFixed(2)}s</p>
            {latestPitch.expected_note && (
              <p>
                Target Assignment:{" "}
                <b style={{ color: "#2196F3" }}>{latestPitch.expected_note}</b>
              </p>
            )}
          </>
        ) : (
          <p style={{ color: "#777" }}>
            Waiting for violin audio input payload streams...
          </p>
        )}
      </div>

      {/* Evaluation Aggregation Panel */}
      {currentScore && (
        <div
          style={{
            marginTop: 40,
            border: "2px solid #4CAF50",
            padding: 20,
            borderRadius: 8,
          }}
        >
          <h2 style={{ color: "#4CAF50" }}>Session Performance Results</h2>
          <h3 style={{ fontSize: 32, margin: "5px 0" }}>
            Total Score: {currentScore.total_score.toFixed(1)}
          </h3>
          <p>
            Intonation/Pitch Accuracy: {currentScore.pitch_accuracy.toFixed(1)}%
          </p>
          <p>
            Rhythmic/Timing Accuracy: {currentScore.timing_accuracy.toFixed(1)}%
          </p>
          <p>
            Notes Executed: {currentScore.notes_hit} /{" "}
            {currentScore.notes_total}
          </p>
        </div>
      )}

      {/* Historical Data Persistence Timeline Panel */}
      <div style={{ marginTop: 40 }}>
        <h3>Historical Performance Analytics (v1.4.0 Persistence Layer)</h3>
        {history.length > 0 ? (
          <table
            style={{ width: "100%", borderCollapse: "collapse", marginTop: 10 }}
          >
            <thead>
              <tr style={{ borderBottom: "2px solid #ccc", textAlign: "left" }}>
                <th style={{ padding: 8 }}>ID</th>
                <th style={{ padding: 8 }}>Date/Time</th>
                <th style={{ padding: 8 }}>Total Score</th>
                <th style={{ padding: 8 }}>Pitch Acc</th>
                <th style={{ padding: 8 }}>Timing Acc</th>
                <th style={{ padding: 8 }}>Notes Hit</th>
              </tr>
            </thead>
            <tbody>
              {history.map((session) => (
                <tr key={session.id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: 8 }}>{session.id}</td>
                  <td style={{ padding: 8, fontSize: 13 }}>
                    {new Date(session.start_time).toLocaleString()}
                  </td>
                  <td style={{ padding: 8, fontWeight: "bold" }}>
                    {session.total_score.toFixed(1)}
                  </td>
                  <td style={{ padding: 8 }}>
                    {session.pitch_accuracy.toFixed(1)}%
                  </td>
                  <td style={{ padding: 8 }}>
                    {session.timing_accuracy.toFixed(1)}%
                  </td>
                  <td style={{ padding: 8 }}>
                    {session.notes_hit} / {session.notes_total}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ color: "#777", fontSize: 14 }}>
            No historical entries found in database.
          </p>
        )}
      </div>
    </div>
  );
}
