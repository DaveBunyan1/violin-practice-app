"use client";

// 1. Updated interface to exactly match score_result schema types
interface PerformanceAnalyticsProps {
  report: {
    message?: string;
    database_id?: number;
    score_result?: {
      total_score: number;
      pitch_accuracy: number;
      timing_accuracy: number;
      notes_hit: number;
      notes_total: number;
    };
    // If you plan on passing the raw notes array inside the report payload later:
    performed_notes?: Array<{
      note: string;
      duration: number;
      avg_pitch_error_cents: number | null;
    }>;
  } | null;
}

export default function PerformanceAnalytics({
  report,
}: PerformanceAnalyticsProps) {
  // Safe extraction helper variable
  const scores = report?.score_result;

  if (!report || !scores) return null;

  return (
    <div
      style={{
        marginTop: 40,
        padding: 24,
        backgroundColor: "#1e1e1e",
        borderRadius: 8,
        border: "1px solid #333",
      }}
    >
      <h3 style={{ margin: "0 0 20px 0", color: "#03DAC6" }}>
        📊 Performance Analysis Summary
      </h3>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 20,
          marginBottom: 24,
        }}
      >
        <div
          style={{
            backgroundColor: "#121212",
            padding: 16,
            borderRadius: 6,
            textAlign: "center",
            border: "1px solid #222",
          }}
        >
          <p style={{ fontSize: 12, color: "#aaa", margin: "0 0 8px 0" }}>
            Overall Accuracy
          </p>
          <span style={{ fontSize: 28, fontWeight: "bold", color: "#BB86FC" }}>
            {/* 2. Map to total_score */}
            {scores.total_score ?? 0}%
          </span>
        </div>

        <div
          style={{
            backgroundColor: "#121212",
            padding: 16,
            borderRadius: 6,
            textAlign: "center",
            border: "1px solid #222",
          }}
        >
          <p style={{ fontSize: 12, color: "#aaa", margin: "0 0 8px 0" }}>
            Pitch Precision
          </p>
          <span style={{ fontSize: 28, fontWeight: "bold", color: "#03DAC6" }}>
            {/* 3. Map to pitch_accuracy */}
            {scores.pitch_accuracy ?? 0}%
          </span>
        </div>

        <div
          style={{
            backgroundColor: "#121212",
            padding: 16,
            borderRadius: 6,
            textAlign: "center",
            border: "1px solid #222",
          }}
        >
          <p style={{ fontSize: 12, color: "#aaa", margin: "0 0 8px 0" }}>
            Timing & Rhythm
          </p>
          <span style={{ fontSize: 28, fontWeight: "bold", color: "#ffb74d" }}>
            {/* 4. Map to timing_accuracy */}
            {scores.timing_accuracy ?? 0}%
          </span>
        </div>
      </div>

      {report.performed_notes && report.performed_notes.length > 0 && (
        <>
          <h4 style={{ color: "#e0e0e0", marginBottom: 12 }}>
            Note Segmentation Details
          </h4>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {report.performed_notes.map((item, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  backgroundColor: "#252525",
                  padding: "10px 16px",
                  borderRadius: 4,
                  fontSize: 14,
                }}
              >
                <div style={{ display: "flex", gap: 16 }}>
                  <span style={{ fontWeight: "bold", color: "#BB86FC" }}>
                    {item.note}
                  </span>
                  <span style={{ color: "#aaa" }}>
                    Duration: {item.duration.toFixed(2)}s
                  </span>
                </div>
                <span
                  style={{
                    color:
                      item.avg_pitch_error_cents === null
                        ? "#aaa"
                        : Math.abs(item.avg_pitch_error_cents) < 15
                          ? "#03DAC6"
                          : "#CF6679",
                    fontWeight: "bold",
                    marginLeft: "auto",
                  }}
                >
                  {item.avg_pitch_error_cents === null
                    ? "Rest"
                    : `${item.avg_pitch_error_cents > 0 ? "+" : ""}${item.avg_pitch_error_cents.toFixed(1)} cents`}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
