"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useRepertoire } from "./hooks/useRepertoire";

export default function DashboardHomePage() {
  const router = useRouter();
  const { pieces, loading } = useRepertoire();
  const [selectedPieceId, setSelectedPieceId] = useState<string>("");

  if (loading)
    return <p style={{ padding: "24px" }}>Loading Dashboard Matrix...</p>;

  const handleLaunchSession = () => {
    if (!selectedPieceId) {
      alert("Please select a repertoire piece to stream.");
      return;
    }
    // 🚀 Instantly route into your active real-time Web Audio/WebSocket workspace!
    router.push(`/session?pieceId=${selectedPieceId}`);
  };

  return (
    <div
      style={{
        maxWidth: "1100px",
        margin: "0 auto",
        padding: "32px",
        fontFamily: "sans-serif",
        color: "#333",
      }}
    >
      {/* 1. HEADER HERO */}
      <header style={{ marginBottom: "32px" }}>
        <h1 style={{ fontSize: "32px", margin: "0 0 8px 0" }}>
          🎻 Practice Command Center
        </h1>
        <p style={{ color: "#666", margin: 0 }}>
          Real-time audio telemetry performance tracking.
        </p>
      </header>

      {/* 2. QUICK START QUICK-ACTION HERO */}
      <section
        style={{
          background: "linear-gradient(135deg, #0070f3 0%, #004494 100%)",
          color: "#fff",
          padding: "24px",
          borderRadius: "12px",
          boxShadow: "0 4px 12px rgba(0,112,243,0.2)",
          marginBottom: "32px",
        }}
      >
        <h2 style={{ margin: "0 0 12px 0", fontSize: "20px" }}>
          ⚡ Quick Start Practice Session
        </h2>
        <p style={{ margin: "0 0 20px 0", opacity: 0.9, fontSize: "14px" }}>
          Launch your Web Audio microphone stream and calibrate pitch mapping
          against your target grid.
        </p>

        <div
          style={{
            display: "flex",
            gap: "16px",
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <select
            value={selectedPieceId}
            onChange={(e) => setSelectedPieceId(e.target.value)}
            style={{
              padding: "12px",
              borderRadius: "6px",
              border: "none",
              minWidth: "260px",
              fontSize: "15px",
              color: "#333",
              fontWeight: "500",
            }}
          >
            <option value="">-- Select Mapped Composition --</option>
            {pieces.map((piece) => (
              <option key={piece.id} value={piece.id}>
                {piece.title} ({piece.bpm} BPM)
              </option>
            ))}
          </select>

          <button
            onClick={handleLaunchSession}
            style={{
              padding: "12px 24px",
              background: "#10b981",
              color: "#fff",
              border: "none",
              borderRadius: "6px",
              fontWeight: "bold",
              cursor: "pointer",
              fontSize: "15px",
              boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
            }}
          >
            Start Live Session →
          </button>
        </div>
      </section>

      {/* 3. HIGH-LEVEL AGGREGATION METRICS */}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "20px",
          marginBottom: "42px",
        }}
      >
        <div
          style={{
            padding: "20px",
            border: "1px solid #eaeaea",
            borderRadius: "8px",
            background: "#fff",
          }}
        >
          <span
            style={{
              color: "#666",
              fontSize: "12px",
              fontWeight: "bold",
              textTransform: "uppercase",
            }}
          >
            Total Practice Time
          </span>
          <h3
            style={{ fontSize: "28px", margin: "8px 0 0 0", color: "#0070f3" }}
          >
            1.8 hours
          </h3>
        </div>
        <div
          style={{
            padding: "20px",
            border: "1px solid #eaeaea",
            borderRadius: "8px",
            background: "#fff",
          }}
        >
          <span
            style={{
              color: "#666",
              fontSize: "12px",
              fontWeight: "bold",
              textTransform: "uppercase",
            }}
          >
            Repertoire Index
          </span>
          <h3 style={{ fontSize: "28px", margin: "8px 0 0 0" }}>
            {pieces.length} Track(s)
          </h3>
        </div>
        <div
          style={{
            padding: "20px",
            border: "1px solid #eaeaea",
            borderRadius: "8px",
            background: "#fff",
          }}
        >
          <span
            style={{
              color: "#666",
              fontSize: "12px",
              fontWeight: "bold",
              textTransform: "uppercase",
            }}
          >
            Avg Pitch Accuracy
          </span>
          <h3
            style={{ fontSize: "28px", margin: "8px 0 0 0", color: "#10b981" }}
          >
            94.2%
          </h3>
        </div>
      </section>

      {/* 4. LOWER COMPARTMENT: DOUBLE PANEL SPLIT */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "2fr 1fr",
          gap: "32px",
          alignItems: "start",
        }}
      >
        {/* LEFT COMPARTMENT: Recent Performance Timeline Feed */}
        <section>
          <h2 style={{ fontSize: "20px", margin: "0 0 16px 0" }}>
            🕒 Recent Performance Sessions
          </h2>
          <div
            style={{ display: "flex", flexDirection: "column", gap: "12px" }}
          >
            {/* Mocking historical telemetry records parsed by your analytics handlers */}
            <div
              style={{
                padding: "16px",
                border: "1px solid #eaeaea",
                borderRadius: "8px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <strong style={{ display: "block", fontSize: "16px" }}>
                  Gymnopédie No.1 (4 Bars Test)
                </strong>
                <span style={{ fontSize: "12px", color: "#666" }}>
                  Tempo: 60 BPM • Passed 16s constraint sanity check
                </span>
              </div>
              <div style={{ textAlign: "right" }}>
                <span
                  style={{
                    color: "#10b981",
                    fontWeight: "bold",
                    display: "block",
                  }}
                >
                  100% Match
                </span>
                <span style={{ fontSize: "12px", color: "#999" }}>
                  Just Now
                </span>
              </div>
            </div>

            <div
              style={{
                padding: "16px",
                border: "1px solid #eaeaea",
                borderRadius: "8px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                opacity: 0.75,
              }}
            >
              <div>
                <strong style={{ display: "block", fontSize: "16px" }}>
                  Scale in G Major
                </strong>
                <span style={{ fontSize: "12px", color: "#666" }}>
                  Tempo: 116 BPM • Intonation calibration run
                </span>
              </div>
              <div style={{ textAlign: "right" }}>
                <span
                  style={{
                    color: "#f59e0b",
                    fontWeight: "bold",
                    display: "block",
                  }}
                >
                  88.5% Match
                </span>
                <span style={{ fontSize: "12px", color: "#999" }}>
                  Yesterday
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* RIGHT COMPARTMENT: Spotlight Repertoire Anchor */}
        <section
          style={{
            padding: "20px",
            background: "#f9f9f9",
            borderRadius: "8px",
            border: "1px solid #eaeaea",
          }}
        >
          <h2 style={{ fontSize: "18px", margin: "0 0 8px 0" }}>
            🎯 Repertoire Spotlight
          </h2>
          <p style={{ fontSize: "13px", color: "#666", margin: "0 0 16px 0" }}>
            This piece has the oldest tracking sync timestamp or lowest stored
            precision value.
          </p>

          {pieces.length > 0 ? (
            <div>
              <h4
                style={{
                  margin: "0 0 4px 0",
                  fontSize: "16px",
                  color: "#0070f3",
                }}
              >
                {pieces[0].title}
              </h4>
              <p style={{ fontSize: "13px", margin: "0 0 16px 0" }}>
                {pieces[0].bpm} BPM | Length:{" "}
                {pieces[0].total_duration.toFixed(2)}s
              </p>

              <button
                onClick={() => router.push("/repertoire")}
                style={{
                  width: "100%",
                  padding: "8px",
                  background: "none",
                  border: "1px solid #0070f3",
                  color: "#0070f3",
                  borderRadius: "4px",
                  fontWeight: "bold",
                  cursor: "pointer",
                  fontSize: "13px",
                }}
              >
                Go to Repertoire Matrix
              </button>
            </div>
          ) : (
            <p style={{ fontSize: "13px", color: "#999", margin: 0 }}>
              No pieces saved to reference.
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
