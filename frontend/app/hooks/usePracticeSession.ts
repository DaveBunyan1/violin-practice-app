import { useState } from "react";
import { PracticeConfig } from "../types/PracticeConfig";
import { startSession } from "../services/session";
import { StartSessionOutput } from "../types/session";

export function usePracticeSession(config: PracticeConfig) {
  const [loading, setLoading] = useState(false);
  const [session, setSession] = useState<StartSessionOutput | null>(null);

  const start = async (pieceId: number) => {
    setLoading(true);

    try {
      const result = await startSession({
        piece_id: pieceId,
        start_bar: config.mode === "passage" ? config.startBar : null,
        end_bar: config.mode === "passage" ? config.endBar : null,
        target_bpm: config.tempo,
      });

      setSession(result);
    } finally {
      setLoading(false);
    }
  };

  return { start, loading, session };
}
