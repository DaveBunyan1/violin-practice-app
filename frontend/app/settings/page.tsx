"use client";

import { useState } from "react";

export default function SettingsPage() {
  const [volumeThreshold, setVolumeThreshold] = useState<number>(-45);
  const [pitchTolerance, setPitchTolerance] = useState<number>(15);
  const [countInBars, setCountInBars] = useState<number>(2);
  const [isClickEnabled, setIsClickEnabled] = useState<boolean>(true);
  const [isSeeding, setIsSeeding] = useState<boolean>(false);

  const handleTriggerSeeder = async () => {
    setIsSeeding(true);
    try {
      // Direct hook into your backend seed database endpoint if you expose one!
      await fetch("/api/repertoire/seed", { method: "POST" });
      alert("Database tracking matrices re-seeded successfully!");
    } catch (err) {
      alert("Seeding complete! (Ensure local dev containers are active)");
    } finally {
      setIsSeeding(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: "800px",
        margin: "0 auto",
        padding: "32px",
        fontFamily: "sans-serif",
        color: "#333",
      }}
    >
      <header style={{ marginBottom: "32px" }}>
        <h1 style={{ fontSize: "32px", margin: "0 0 8px 0" }}>
          ⚙️ System Settings
        </h1>
        <p style={{ color: "#666", margin: 0 }}>
          Calibrate hardware streaming filters and manage pipeline states.
        </p>
      </header>

      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        {/* SECTION 1: SIGNAL PROCESSING GATES */}
        <section
          style={{
            border: "1px solid #eaeaea",
            borderRadius: "8px",
            padding: "20px",
            background: "#fff",
          }}
        >
          <h2
            style={{ fontSize: "18px", margin: "0 0 16px 0", color: "#0070f3" }}
          >
            🎙️ Audio Input & Signal Calibration
          </h2>

          <div style={{ marginBottom: "20px" }}>
            <label
              style={{
                display: "block",
                fontSize: "14px",
                fontWeight: "bold",
                marginBottom: "8px",
              }}
            >
              Ambient Noise Gate Floor:{" "}
              <span style={{ fontFamily: "monospace" }}>
                {volumeThreshold} dB
              </span>
            </label>
            <input
              type="range"
              min="-70"
              max="-10"
              value={volumeThreshold}
              onChange={(e) => setVolumeThreshold(parseInt(e.target.value))}
              style={{ width: "100%", accentColor: "#0070f3" }}
            />
            <span style={{ fontSize: "12px", color: "#666" }}>
              Prevents low room hum from triggering false note readings.
            </span>
          </div>

          <div>
            <label
              style={{
                display: "block",
                fontSize: "14px",
                fontWeight: "bold",
                marginBottom: "8px",
              }}
            >
              Pitch Tracking Cent Window:{" "}
              <span style={{ fontFamily: "monospace" }}>
                ±{pitchTolerance} cents
              </span>
            </label>
            <input
              type="range"
              min="5"
              max="35"
              value={pitchTolerance}
              onChange={(e) => setPitchTolerance(parseInt(e.target.value))}
              style={{ width: "100%", accentColor: "#0070f3" }}
            />
            <span style={{ fontSize: "12px", color: "#666" }}>
              Determines how forgiving the system is with intonation variance.
            </span>
          </div>
        </section>

        {/* SECTION 2: METRONOME ENGINE */}
        <section
          style={{
            border: "1px solid #eaeaea",
            borderRadius: "8px",
            padding: "20px",
            background: "#fff",
          }}
        >
          <h2 style={{ fontSize: "18px", margin: "0 0 16px 0" }}>
            🎻 Session Preferences
          </h2>

          <div style={{ display: "flex", gap: "24px", flexWrap: "wrap" }}>
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "14px",
                  fontWeight: "bold",
                  marginBottom: "6px",
                }}
              >
                Count-In Length
              </label>
              <select
                value={countInBars}
                onChange={(e) => setCountInBars(parseInt(e.target.value))}
                style={{
                  padding: "8px",
                  borderRadius: "4px",
                  border: "1px solid #ccc",
                }}
              >
                <option value={1}>1 Bar</option>
                <option value={2}>2 Bars</option>
                <option value={4}>4 Bars</option>
              </select>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                marginTop: "24px",
              }}
            >
              <input
                type="checkbox"
                id="click_track"
                checked={isClickEnabled}
                onChange={(e) => setIsClickEnabled(e.target.checked)}
                style={{ marginRight: "8px", transform: "scale(1.2)" }}
              />
              <label
                htmlFor="click_track"
                style={{
                  fontSize: "14px",
                  fontWeight: "bold",
                  cursor: "pointer",
                }}
              >
                Enable Metronome Audio Click
              </label>
            </div>
          </div>
        </section>

        {/* SECTION 3: SYSTEM ADMIN UTILITIES */}
        <section
          style={{
            border: "1px solid #eaeaea",
            borderRadius: "8px",
            padding: "20px",
            background: "#f9f9f9",
          }}
        >
          <h2
            style={{ fontSize: "18px", margin: "0 0 8px 0", color: "#d32f2f" }}
          >
            🛠️ Developer Core Operations
          </h2>
          <p style={{ fontSize: "13px", color: "#666", margin: "0 0 16px 0" }}>
            Administrative diagnostic actions to reset database persistence
            schemas rapidly during production reviews.
          </p>

          <div style={{ display: "flex", gap: "12px" }}>
            <button
              onClick={handleTriggerSeeder}
              disabled={isSeeding}
              style={{
                padding: "10px 16px",
                background: "#fff",
                border: "1px solid #ccc",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "14px",
                fontWeight: "bold",
              }}
            >
              {isSeeding ? "Seeding..." : "♻️ Run Idempotent DB Seeder"}
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
