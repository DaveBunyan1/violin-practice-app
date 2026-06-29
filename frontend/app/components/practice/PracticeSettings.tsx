"use client";

interface Props {
  tempo: number;
  setTempo: (n: number) => void;

  countdown: number;
  setCountdown: (n: number) => void;

  metronome: boolean;
  setMetronome: (b: boolean) => void;

  tuner: boolean;
  setTuner: (b: boolean) => void;
}

export default function PracticeSettings({
  tempo,
  setTempo,
  countdown,
  setCountdown,
  metronome,
  setMetronome,
  tuner,
  setTuner,
}: Props) {
  return (
    <>
      {/* TEMPO */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <label style={{ fontWeight: "bold" }}>Tempo:</label>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="number"
            min={40}
            max={240}
            value={tempo}
            onChange={(e) => setTempo(Number(e.target.value))}
            style={{ width: 80, padding: 8 }}
          />
          <span>BPM</span>
        </div>
      </div>

      {/* COUNTDOWN */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <label style={{ fontWeight: "bold" }}>Countdown:</label>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="number"
            min={0}
            max={10}
            value={countdown}
            onChange={(e) => setCountdown(Number(e.target.value))}
            style={{ width: 80, padding: 8 }}
          />
          <span>seconds</span>
        </div>
      </div>

      {/* TOGGLES */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <label style={{ display: "flex", gap: 8 }}>
          <input
            type="checkbox"
            checked={metronome}
            onChange={(e) => setMetronome(e.target.checked)}
          />
          Metronome Enabled
        </label>

        <label style={{ display: "flex", gap: 8 }}>
          <input
            type="checkbox"
            checked={tuner}
            onChange={(e) => setTuner(e.target.checked)}
          />
          Tuner Enabled
        </label>
      </div>
    </>
  );
}
