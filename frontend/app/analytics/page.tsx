"use client";

import React, { useState } from "react";
import { useAnalytics } from "../hooks/useAnalytics";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

export default function AnalyticsPage() {
  const { data, loading, error } = useAnalytics();
  const [selectedPieceId, setSelectedPieceId] = useState<number | "all">("all");

  if (loading)
    return (
      <div style={containerStyle}>
        <p>Gathering practice timeline data...</p>
      </div>
    );
  if (error)
    return (
      <div style={containerStyle}>
        <p style={{ color: "#FF5252" }}>Error: {error}</p>
      </div>
    );
  if (data.length === 0) {
    return (
      <div style={containerStyle}>
        <h2>No Practice Records Found</h2>
        <p style={{ color: "#aaa" }}>
          Complete a practice run to start logging statistics.
        </p>
      </div>
    );
  }

  // ==========================================
  // 🌟 FILTERING BY PIECE
  // ==========================================
  // Deduplicate pieces we have records for
  const uniquePieces = Array.from(new Set(data.map((s) => s.piece_id))).filter(
    Boolean,
  );

  const filteredData =
    selectedPieceId === "all"
      ? data
      : data.filter((s) => s.piece_id === selectedPieceId);

  const totalSessions = filteredData.length;
  if (totalSessions === 0)
    return (
      <div style={containerStyle}>
        <p>No data for this piece.</p>
      </div>
    );

  const avgTotalScore = Math.round(
    filteredData.reduce((acc, s) => acc + s.total_score, 0) / totalSessions,
  );
  const avgPitchAcc = Math.round(
    filteredData.reduce((acc, s) => acc + s.pitch_accuracy, 0) / totalSessions,
  );
  const avgTimingAcc = Math.round(
    filteredData.reduce((acc, s) => acc + s.timing_accuracy, 0) / totalSessions,
  );

  const totalPracticeMinutes = Math.round(
    filteredData.reduce((acc, s) => {
      if (!s.end_time) return acc;
      const durationMs =
        new Date(s.end_time).getTime() - new Date(s.start_time).getTime();
      return acc + Math.max(0, durationMs / 1000 / 60);
    }, 0),
  );

  const chartData = filteredData.map((s) => ({
    ...s,
    date: new Date(s.start_time).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
    }),
  }));

  // ==========================================
  // 🌟 HARDCODED TROUBLESHOOTING DIAGNOSTIC FOR TOMORROW
  // ==========================================
  const lastSession = filteredData[filteredData.length - 1];

  // Custom heuristics based on last session scores to find troublesome segments
  const getTroublesomeBars = () => {
    if (!lastSession) return [];
    const bars: string[] = [];

    if (lastSession.pitch_accuracy < 85) {
      bars.push("Bar 5-8 (Intonation shifts on high registers felt unstable)");
    }
    if (lastSession.timing_accuracy < 80) {
      bars.push("Bar 12-14 (Rhythm dragged during slow tempo transitions)");
    }
    if (lastSession.notes_hit / lastSession.notes_total < 0.85) {
      bars.push("Bar 2 & 3 (Missing entry markers entirely)");
    }

    // Default fallback if you played beautifully!
    if (bars.length === 0) {
      bars.push(
        "No major problem areas found! Try increasing your target tempo config by +5 BPM.",
      );
    }
    return bars;
  };

  return (
    <div style={containerStyle}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "24px",
        }}
      >
        <div>
          <h1 style={{ margin: "0 0 4px 0", fontSize: "28px" }}>
            Practice Insights
          </h1>
          <p style={{ color: "#aaa", margin: 0 }}>
            Review feedback loops to optimize tomorrow's routine.
          </p>
        </div>

        {/* 🌟 PIECE SELECTOR DROPDOWN */}
        <select
          value={selectedPieceId}
          onChange={(e) =>
            setSelectedPieceId(
              e.target.value === "all" ? "all" : Number(e.target.value),
            )
          }
          style={dropdownStyle}
        >
          <option value="all">📁 All Repertoire Combined</option>
          {uniquePieces.map((id) => (
            <option key={id} value={id}>
              🎻 Piece Profile Record #{id}
            </option>
          ))}
        </select>
      </div>

      {/* 1. AGGREGATE SUMMARY GRID */}
      <div style={statsGridStyle}>
        <div style={cardStyle}>
          <span style={labelStyle}>Sessions</span>
          <h2 style={valueStyle}>{totalSessions}</h2>
        </div>
        <div style={cardStyle}>
          <span style={labelStyle}>Duration Logged</span>
          <h2 style={valueStyle}>
            {totalPracticeMinutes || "< 1"}{" "}
            <span style={{ fontSize: "14px", color: "#aaa" }}>mins</span>
          </h2>
        </div>
        <div style={cardStyle}>
          <span style={labelStyle}>Avg Score</span>
          <h2 style={{ ...valueStyle, color: "#03DAC6" }}>{avgTotalScore}%</h2>
        </div>
        <div style={cardStyle}>
          <span style={labelStyle}>Intonation vs Rhythm</span>
          <h3 style={{ margin: "4px 0 0 0", color: "#fff", fontSize: "16px" }}>
            🎯 {avgPitchAcc}% <span style={{ color: "#444" }}>|</span> ⏱️{" "}
            {avgTimingAcc}%
          </h3>
        </div>
      </div>

      {/* 2. TOMORROW'S TARGET TARGETS (TROUBLESOME BARS DIAGNOSTIC) */}
      <div
        style={{
          ...cardStyle,
          borderColor: "#FFC107",
          backgroundColor: "#1F1A0F",
          marginBottom: "32px",
          padding: "20px",
        }}
      >
        <h3
          style={{
            margin: "0 0 8px 0",
            fontSize: "15px",
            color: "#FFC107",
            display: "flex",
            alignItems: "center",
            gap: "6px",
          }}
        >
          ⚠️ Targeted Directives for Next Session
        </h3>
        <p style={{ margin: "0 0 12px 0", fontSize: "14px", color: "#ccc" }}>
          Based on metrics parsed from your last run (Score: **
          {lastSession?.total_score}%**), isolate these chunks before playing
          the whole piece:
        </p>
        <ul
          style={{
            margin: 0,
            paddingLeft: "20px",
            color: "#fff",
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            fontSize: "14px",
          }}
        >
          {getTroublesomeBars().map((bar, i) => (
            <li key={i} style={{ lineHeight: "1.4" }}>
              {bar}
            </li>
          ))}
        </ul>
      </div>

      {/* 3. PROGRESSION TIMELINE CHART */}
      <div style={{ ...cardStyle, padding: "24px", height: "340px" }}>
        <h3 style={{ margin: "0 0 20px 0", fontSize: "15px", color: "#fff" }}>
          Performance Trend Curves
        </h3>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 20, left: -20, bottom: 25 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#222" />
            <XAxis dataKey="date" stroke="#666" style={{ fontSize: "11px" }} />
            <YAxis
              domain={[0, 100]}
              stroke="#666"
              style={{ fontSize: "11px" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#141419",
                border: "1px solid #333",
                borderRadius: "6px",
              }}
            />
            <Legend wrapperStyle={{ paddingTop: "10px", fontSize: "13px" }} />
            <Line
              type="monotone"
              dataKey="total_score"
              name="Overall"
              stroke="#03DAC6"
              strokeWidth={2.5}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="pitch_accuracy"
              name="Pitch Intonation"
              stroke="#4CAF50"
              strokeWidth={1.5}
              strokeDasharray="3 3"
            />
            <Line
              type="monotone"
              dataKey="timing_accuracy"
              name="Rhythm & Pace"
              stroke="#FFC107"
              strokeWidth={1.5}
              strokeDasharray="3 3"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// Minimalistic styling helpers
const containerStyle: React.CSSProperties = {
  maxWidth: "900px",
  margin: "0 auto",
  padding: "40px 24px",
  color: "#fff",
  minHeight: "100vh",
};
const statsGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
  gap: "16px",
  marginBottom: "32px",
};
const cardStyle: React.CSSProperties = {
  backgroundColor: "#1E1E24",
  border: "1px solid #2D2D35",
  borderRadius: "12px",
  padding: "16px",
  display: "flex",
  flexDirection: "column",
  justifyContent: "center",
};
const labelStyle: React.CSSProperties = {
  fontSize: "11px",
  color: "#aaa",
  textTransform: "uppercase",
  letterSpacing: "0.5px",
};
const valueStyle: React.CSSProperties = {
  margin: "2px 0 0 0",
  fontSize: "26px",
  fontWeight: "bold",
};
const dropdownStyle: React.CSSProperties = {
  backgroundColor: "#1E1E24",
  color: "#fff",
  border: "1px solid #333",
  borderRadius: "8px",
  padding: "10px 14px",
  fontSize: "14px",
  cursor: "pointer",
  outline: "none",
};
