// app/hooks/useAnalytics.ts
import { useState, useEffect } from "react";

export interface HistoricalSession {
  id: number;
  piece_id: number;
  start_time: string;
  end_time: string | null;
  total_score: number;
  pitch_accuracy: number;
  timing_accuracy: number;
  notes_hit: number;
  notes_total: number;
}

export function useAnalytics() {
  const [data, setData] = useState<HistoricalSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const res = await fetch(
          "http://localhost:8000/session/sessions?limit=50",
        );
        if (!res.ok) throw new Error("Failed to fetch tracking metrics.");
        const json = await res.json();
        // Backend returns newest first; reverse for chronological left-to-right graphs
        setData(json.reverse());
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, []);

  return { data, loading, error };
}
