"use client";

import { useEffect, useState } from "react";

type PitchData = {
  frequency: number;
  note: string;
  time: number;
};

const HOST = process.env.NEXT_PUBLIC_WEBSOCKET_HOST;
const PORT = process.env.NEXT_PUBLIC_WEBSOCKET_PORT;

const piece = [
  { note: "A4", time: 0 },
  { note: "B4", time: 2 },
  { note: "C#5", time: 4 },
  { note: "D5", time: 6 },
];

export default function Page() {
  const [data, setData] = useState<PitchData | null>(null);
  const [connected, setConnected] = useState(false);
  const [time, setTime] = useState(0);
  const [mockNote, setMockNote] = useState<string | null>(null);

  useEffect(() => {
    const mock = setInterval(() => {
      const notes = ["A4", "B4", "C#5", "D5", "E5"];
      const random = notes[Math.floor(Math.random() * notes.length)];
      setMockNote(random);
    }, 500);

    return () => clearInterval(mock);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setTime((t) => t + 0.1);
    }, 100);

    return () => clearInterval(interval);
  });

  const expected = piece.find((n) => time >= n.time && time < n.time + 2);
  const isCorrect = expected?.note === mockNote;

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

      <div>
        <p>Time: {time.toFixed(1)}</p>
        <p>Expected: {expected?.note ?? "None"}</p>
        <p>Detected (mock): {mockNote}</p>
        <p style={{ color: isCorrect ? "green" : "red" }}>
          {isCorrect ? "Correct" : "Incorrect"}
        </p>
      </div>
    </div>
  );
}
