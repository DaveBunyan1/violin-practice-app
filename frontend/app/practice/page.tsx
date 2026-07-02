// TODO: Refactor Analytics Transition Lifecycle
// -------------------------------------------------------------------------
// CURRENT WORKFLOW:
// activeCanvas -> isProcessingEnd (Full Screen Overlay) -> showResults (Stats)
//
// OPTIMIZED FUTURE TARGET UX:
// 1. Fire handleEndSession() and instantly set showResults(true).
// 2. Pass an `isLoading={isProcessingReport}` flag directly into <PerformanceAnalytics />.
// 3. Inside <PerformanceAnalytics />, if isLoading is true, render a beautiful
//    "Calculating Metrics..." spinning sub-panel or skeleton blocks inside the grid.
// 4. This keeps layout shifting to a minimum and gives immediate visual feedback
//    that their performance data has been captured and is being processed.
// -------------------------------------------------------------------------
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
    reset,
    status,
    loading: sessionLoading,
    active,
  } = usePracticeSession(config);

  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const [countdownSeconds, setCountdownSeconds] = useState<number | null>(null);
  const [sessionReport, setSessionReport] = useState<any | null>(null);
  const [showResults, setShowResults] = useState<boolean>(false);

  const [isProcessingEnd, setIsProcessingEnd] = useState<boolean>(false);
  const animationRef = useRef<number | null>(null);
  const lastFrameTimeRef = useRef<number | null>(null);
  const countdownIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isEndingRef = useRef<boolean>(false);

  const updateTimelineCursor = (timestamp: number) => {
    if (!selectedPiece || isEndingRef.current) return;

    if (lastFrameTimeRef.current === null) {
      lastFrameTimeRef.current = timestamp;
      animationRef.current = requestAnimationFrame(updateTimelineCursor);
      return;
    }
    const realDeltaTimeSeconds = (timestamp - lastFrameTimeRef.current) / 1000;
    lastFrameTimeRef.current = timestamp;

    const originalBpm = selectedPiece.bpm || 116;
    const practiceBpm = config.tempo || originalBpm;
    const speedMultiplier = practiceBpm / originalBpm;

    let baseDuration =
      (selectedPiece.total_duration || 60) * (originalBpm / practiceBpm);

    if (config.mode === "passage" && config.startBar && config.endBar) {
      const timeSigNumerator = selectedPiece.time_signature_numerator || 4;
      const beatDuration = 60 / practiceBpm;
      const barDuration = beatDuration * timeSigNumerator;
      const totalPassageBars =
        Number(config.endBar) - Number(config.startBar) + 1;

      baseDuration = totalPassageBars * barDuration;
    }

    setElapsedTime((prevElapsed) => {
      const nextElapsed = prevElapsed + realDeltaTimeSeconds;
      const executionCeiling = baseDuration + 1.5;

      // Auto-trigger session completion when cursor crosses end bounds
      if (nextElapsed >= executionCeiling && !isEndingRef.current) {
        handleEndSession();
        return selectedPiece.total_duration || 60;
      }
      return nextElapsed;
    });

    animationRef.current = requestAnimationFrame(updateTimelineCursor);
  };

  useEffect(() => {
    if (active) {
      setShowResults(false);
      setSessionReport(null);

      if (config.countdown && config.countdown > 0) {
        setCountdownSeconds(config.countdown);

        countdownIntervalRef.current = setInterval(() => {
          setCountdownSeconds((prev) => {
            if (prev === null || prev <= 1) {
              clearInterval(countdownIntervalRef.current!);
              lastFrameTimeRef.current = null;
              setElapsedTime(0);
              animationRef.current =
                requestAnimationFrame(updateTimelineCursor);
              return null;
            }
            return prev - 1;
          });
        }, 1000);
      } else {
        lastFrameTimeRef.current = null;
        setElapsedTime(0);
        animationRef.current = requestAnimationFrame(updateTimelineCursor);
      }
    } else {
      cleanupLoops();
    }

    return () => cleanupLoops();
  }, [active]);

  const cleanupLoops = () => {
    if (animationRef.current) cancelAnimationFrame(animationRef.current);
    if (countdownIntervalRef.current)
      clearInterval(countdownIntervalRef.current);
    setCountdownSeconds(null);
    lastFrameTimeRef.current = null;
  };

  const handleStartSession = async () => {
    if (!selectedPiece) return;

    reset();
    isEndingRef.current = false;
    setShowResults(false);
    setSessionReport(null);

    await start(selectedPiece.id, config.countdown ?? 0);
  };

  const handleEndSession = async () => {
    if (isEndingRef.current) return;
    isEndingRef.current = true;

    setIsProcessingEnd(true);

    cleanupLoops();

    const resultReport = await end();
    if (resultReport) {
      setSessionReport(resultReport);
    } else {
      // Fallback mockup generator for immediate standalone local validation:
      setSessionReport({
        score_result: {
          total_score: 85,
          pitch_accuracy: 88,
          timing_accuracy: 82,
          notes_hit: 14,
          notes_total: 16,
        },
        performed_notes: [
          { note: "G4", duration: 1.2, avg_pitch_error_cents: 4.2 },
          { note: "D4", duration: 0.9, avg_pitch_error_cents: -18.4 },
        ],
      });
    }
    setIsProcessingEnd(false);
    setShowResults(true);
  };

  if (repertoireLoading) return <p>Loading...</p>;

  // =========================================================
  // VIEW PHASE 1: RESULTS DASHBOARD SUMMARY
  // =========================================================
  if (showResults && sessionReport) {
    return (
      <div style={{ maxWidth: 600, margin: "40px auto", padding: "0 16px" }}>
        <h1 style={{ textAlign: "center", marginBottom: 8 }}>
          Session Completed
        </h1>
        <p style={{ textAlign: "center", color: "#aaa", margin: "0 0 24px 0" }}>
          Great job practicing {selectedPiece?.title}! Here is your analysis:
        </p>

        <PerformanceAnalytics report={sessionReport} />

        {/* Workflow Navigation Controls */}
        <div style={{ display: "flex", gap: 16, marginTop: 24 }}>
          <button
            onClick={() => setShowResults(false)} // Return back to the setup config panel
            style={{
              flex: 1,
              padding: "14px",
              backgroundColor: "#232329",
              color: "#fff",
              border: "1px solid #333",
              borderRadius: "8px",
              cursor: "pointer",
              fontWeight: "600",
            }}
          >
            ⚙️ Change Settings
          </button>

          <button
            onClick={handleStartSession} // Re-fire same configs instantly
            style={{
              flex: 1,
              padding: "14px",
              backgroundColor: "#03DAC6",
              color: "#000",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            🔄 Practice Again
          </button>
        </div>
      </div>
    );
  }

  // =========================================================
  // VIEW PHASE 2: ACTIVE MUSIC PERFORMANCE CANVAS
  // =========================================================
  if ((active || isProcessingEnd) && selectedPiece) {
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
  // VIEW 3: SETUP CONFIGURATION MENU STATE
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
