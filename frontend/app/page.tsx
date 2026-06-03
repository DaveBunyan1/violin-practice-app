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
