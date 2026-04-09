"use client";

import { useEffect, useState } from "react";

type PitchData = {
  frequency: number;
  note: string;
  time: number;
};

const HOST = process.env.NEXT_PUBLIC_WEBSOCKET_HOST;
const PORT = process.env.NEXT_PUBLIC_WEBSOCKET_PORT;

export default function Page() {
  const [data, setData] = useState<PitchData | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(`ws://${HOST}:${PORT}`);

    ws.onopen = () => {
      console.log("Connected to backend");
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      setData(msg.data); // matches your backend structure
    };

    ws.onclose = () => {
      console.log("Disconnected");
      setConnected(false);
    };

    return () => ws.close();
  }, []);

  return (
    <div style={{ padding: 40, fontFamily: "sans-serif" }}>
      <h1>🎻 Violin Tuner</h1>

      <p>Status: {connected ? "🟢 Connected" : "🔴 Disconnected"}</p>

      {data ? (
        <div style={{ marginTop: 20 }}>
          <h2 style={{ fontSize: 48 }}>{data.note}</h2>
          <p>{data.frequency.toFixed(2)} Hz</p>
          <p>{new Date(data.time * 1000).toLocaleTimeString()}</p>
        </div>
      ) : (
        <p>Waiting for signal...</p>
      )}
    </div>
  );
}
