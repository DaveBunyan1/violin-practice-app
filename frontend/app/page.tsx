"use client";

import { useEffect, useState } from "react";

type PitchData = {
  frequency: number;
  note: string;
  time: number;
  expected_note?: string;
};

const HOST = process.env.NEXT_PUBLIC_WEBSOCKET_HOST;
const PORT = process.env.NEXT_PUBLIC_WEBSOCKET_PORT;

export default function Page() {
  const [connected, setConnected] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [latest, setLatest] = useState<PitchData | null>(null);
  const [score, setScore] = useState<any>(null);

  useEffect(() => {
    const socket = new WebSocket(`ws://${HOST}:${PORT}`);

    socket.onopen = () => {
      console.log("Connected to backend");
      setConnected(true);
    };

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "pitch") {
        setLatest(msg.data);
      }

      if (msg.type === "score_result") {
        setScore(msg.data);
      }
    };

    socket.onclose = () => {
      console.log("Disconnected");
      setConnected(false);
    };

    setWs(socket);

    return () => socket.close();
  }, []);

  const startSession = () => {
    if (!ws) return;

    ws.send(
      JSON.stringify({
        type: "start_session",
      }),
    );
  };

  const endSession = () => {
    if (!ws) return;

    ws.send(
      JSON.stringify({
        type: "end_session",
      }),
    );
  };

  return (
    <div style={{ padding: 40, fontFamily: "sans-serif" }}>
      <h1>🎻 Violin Practice</h1>

      <p>Status: {connected ? "🟢 Connected" : "🔴 Disconnected"}</p>

      <button
        onClick={startSession}
        style={{
          marginTop: 20,
          padding: "10px 20px",
          fontSize: 16,
        }}
      >
        ▶ Start Session
      </button>

      <button
        onClick={endSession}
        style={{
          marginTop: 10,
          padding: "10px 20px",
          fontSize: 16,
          backgroundColor: "#f44336",
          color: "white",
        }}
      >
        ⏹ End Session
      </button>

      {score && (
        <div style={{ marginTop: 40 }}>
          <h2>Score: {score.total_score}</h2>
          <p>Pitch: {score.pitch_accuracy}%</p>
          <p>Timing: {score.timing_accuracy}%</p>
        </div>
      )}

      <div style={{ marginTop: 40 }}>
        {latest ? (
          <>
            <h2 style={{ fontSize: 48 }}>{latest.note}</h2>
            <p>Freq: {latest.frequency.toFixed(2)} Hz</p>
            <p>Time: {latest.time.toFixed(2)}s</p>

            {latest.expected_note && (
              <p>
                Expected: <b>{latest.expected_note}</b>
              </p>
            )}
          </>
        ) : (
          <p>Waiting for signal...</p>
        )}
      </div>
    </div>
  );
}
