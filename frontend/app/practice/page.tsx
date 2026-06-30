"use client";

import { useEffect, useState, useRef } from "react";
import PracticeForm from "../components/practice/PracticeForm";
import ActiveSessionCanvas from "../components/practice/ActiveSessionCanvas";
import PerformanceAnalytics from "../components/practice/PerformanceAnalytics";
import { usePracticeConfig } from "../hooks/usePracticeConfig";
import { usePracticeSession } from "../hooks/usePracticeSession";
import { useRepertoire } from "../hooks/useRepertoire";

export default function PracticePage() {
  const {
    pieces,
    selectedPiece,
    selectPiece,
    loading: repertoireLoading,
  } = useRepertoire();
  const { config, setConfig } = usePracticeConfig();
  const {
    start,
    end,
    status,
    loading: sessionLoading,
    active,
  } = usePracticeSession(config);

  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const [countdownSeconds, setCountdownSeconds] = useState<number | null>(null);
  const [sessionReport, setSessionReport] = useState<any | null>(null);
  const [showResults, setShowResults] = useState<boolean>(false);

  const animationRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const countdownIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const updateTimelineCursor = (timestamp: number) => {
    if (!startTimeRef.current || !selectedPiece) return;
    const elapsed = (timestamp - startTimeRef.current) / 1000;

    const originalBpm = selectedPiece.bpm || 116;
    const practiceBpm = config.tempo || originalBpm;
    const timeScaleFactor = originalBpm / practiceBpm;
    const adjustedTotalDuration =
      (selectedPiece.total_duration || 60) * timeScaleFactor;

    if (elapsed >= adjustedTotalDuration) {
      handleEndSession();
    } else {
      setElapsedTime(elapsed);
      animationRef.current = requestAnimationFrame(updateTimelineCursor);
    }
  };

  useEffect(() => {
    if (active) {
      // 1. Check if user enabled a countdown buffer
      if (config.countdown && config.countdown > 0) {
        setCountdownSeconds(config.countdown);

        countdownIntervalRef.current = setInterval(() => {
          setCountdownSeconds((prev) => {
            if (prev === null || prev <= 1) {
              clearInterval(countdownIntervalRef.current!);

              // Countdown complete -> Fire up the timeline cursor
              startTimeRef.current = performance.now();
              animationRef.current =
                requestAnimationFrame(updateTimelineCursor);
              return null; // Clears visual countdown shield overlay
            }
            return prev - 1;
          });
        }, 1000);
      } else {
        // 2. No countdown enabled -> Kickoff tracking loop instantly
        setElapsedTime(0);
        startTimeRef.current = performance.now();
        animationRef.current = requestAnimationFrame(updateTimelineCursor);
      }
    } else {
      // Cleanup running tracking loops when session terminates
      cleanupLoops();
    }

    return () => cleanupLoops();
  }, [active]);

  const cleanupLoops = () => {
    if (animationRef.current) cancelAnimationFrame(animationRef.current);
    if (countdownIntervalRef.current)
      clearInterval(countdownIntervalRef.current);
    setCountdownSeconds(null);
  };
  const handleStartSession = async () => {
    if (!selectedPiece) return;
    await start(selectedPiece.id);
  };

  const handleEndSession = async () => {
    await end();
    cleanupLoops();
  };

  if (repertoireLoading) return <p>Loading...</p>;

  // ==========================================
  // VIEW 1: ACTIVE LIVE PRE-PLAY OR PLAY STATE
  // ==========================================
  if (active && selectedPiece) {
    const practiceBpm = config.tempo || selectedPiece.bpm;
    return (
      <div style={{ position: "relative", minHeight: "100vh", width: "100%" }}>
        {countdownSeconds !== null && (
          <div
            style={{
              position: "fixed",
              top: 0,
              left: 0,
              width: "100vw",
              height: "100vh",
              backgroundColor: "rgba(18, 18, 18, 0.95)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 9999,
              userSelect: "none",
            }}
          >
            <span
              style={{
                fontSize: "14px",
                color: "#666",
                fontWeight: "bold",
                letterSpacing: "2px",
                textTransform: "uppercase",
              }}
            >
              Get Ready
            </span>
            <h1
              style={{ fontSize: "120px", color: "#03DAC6", margin: "20px 0" }}
            >
              {countdownSeconds}
            </h1>
            <p style={{ color: "#aaa", fontSize: "16px" }}>
              Target Tempo: {practiceBpm} BPM
            </p>
          </div>
        )}
        <ActiveSessionCanvas
          selectedPiece={selectedPiece}
          practiceBpm={practiceBpm}
          config={config}
          elapsedTime={elapsedTime}
          isActive={active}
          onEndSession={handleEndSession}
        />
      </div>
    );
  }

  // ==========================================
  // VIEW 2: SETUP CONFIGURATION MENU STATE
  // ==========================================
  return (
    <PracticeForm
      pieces={pieces}
      selectedPiece={selectedPiece}
      config={config}
      sessionLoading={sessionLoading}
      status={status}
      onPieceSelect={selectPiece}
      onConfigChange={setConfig}
      onStartSession={handleStartSession}
    />
  );
}
