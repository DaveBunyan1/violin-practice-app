import { useState } from "react";
import { PracticeConfig } from "../types/PracticeConfig";
import { startSession } from "../services/session";
import { PracticeSession, SessionStatus } from "../types/session";

export function usePracticeSession(config: PracticeConfig) {
  const [status, setStatus] = useState<SessionStatus>("idle");
  const [session, setSession] = useState<PracticeSession | null>(null);
  const [error, setError] = useState<string | null>(null);

  const start = async (pieceId: number) => {
    if (status !== "idle" && status !== "ended") return;

    setStatus("starting");
    setError(null);

    try {
      const res = await startSession({
        piece_id: pieceId,
        start_bar: config.mode === "passage" ? config.startBar : null,
        end_bar: config.mode === "passage" ? config.endBar : null,
        target_bpm: config.tempo,
      });

      setSession({
        status: "active",
        sessionId: res.session_id, // if backend adds later
        startedAt: Date.now(),
      });

      setStatus("active");
    } catch (e: any) {
      setStatus("error");
      setError(e?.message ?? "Failed to start session");
    }
  };

  const end = async () => {
    if (status !== "active") return;

    setStatus("ending");

    try {
      await fetch("http://localhost:8000/session/end", {
        method: "POST",
      });

      setSession((prev) =>
        prev
          ? {
              ...prev,
              status: "ended",
              endedAt: Date.now(),
            }
          : null,
      );

      setStatus("ended");
    } catch (e: any) {
      setStatus("error");
      setError(e?.message ?? "Failed to end session");
    }
  };

  const reset = () => {
    setStatus("idle");
    setSession(null);
    setError(null);
  };

  return {
    start,
    end,
    reset,
    status,
    session,
    error,
    loading: status === "starting",
    active: status === "active",
  };
}
