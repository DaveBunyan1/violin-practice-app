"use client";

interface TargetNote {
  note: string;
  time: number;
  duration: number;
}

interface TimelineCanvasProps {
  notes: TargetNote[];
  totalDuration: number;
  elapsedTime: number;
  isSessionActive: boolean;
}

export default function TimelineCanvas({
  notes,
  totalDuration,
  elapsedTime,
  isSessionActive,
}: TimelineCanvasProps) {
  const playbackPercentage = totalDuration
    ? (elapsedTime / totalDuration) * 100
    : 0;

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "200px",
        backgroundColor: "#1e1e1e",
        borderRadius: 8,
        border: "1px solid #333",
        overflow: "hidden",
        marginTop: 20,
      }}
    >
      {/* Target Note Row Blocks */}
      {notes.map((note, index) => {
        const leftPercent = (note.time / totalDuration) * 100;
        const widthPercent = (note.duration / totalDuration) * 100;

        return (
          <div
            key={index}
            style={{
              position: "absolute",
              left: `${leftPercent}%`,
              width: `${widthPercent}%`,
              top: "35%",
              height: "50px",
              backgroundColor: "#3700B3",
              border: "2px solid #BB86FC",
              borderRadius: 6,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 14,
              fontWeight: "bold",
              color: "#fff",
              boxSizing: "border-box",
            }}
          >
            {note.note}
          </div>
        );
      })}

      {/* Smooth Moving Playback Cursor Line */}
      <div
        style={{
          position: "absolute",
          left: `${playbackPercentage}%`,
          top: 0,
          width: "3px",
          height: "100%",
          backgroundColor: "#03DAC6",
          boxShadow: "0 0 10px #03DAC6",
          transition: isSessionActive ? "none" : "left 0.1s linear",
          zIndex: 10,
        }}
      />
    </div>
  );
}
