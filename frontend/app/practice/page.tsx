"use client";

import { Piece } from "../types/Piece";

import PieceSelector from "../components/practice/PieceSelector";
import PracticeModeSelector from "../components/practice/PracticeModeSelector";
import PassageSelector from "../components/practice/PassageSelector";
import PracticeSettings from "../components/practice/PracticeSettings";
import StartPracticeButton from "../components/practice/StartPracticeButton";
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
  // Load repertoire once on mount

  const handlePieceSelected = (piece: Piece) => {
    selectPiece(piece);

    setConfig((prev) => ({
      ...prev,
      tempo: piece.bpm,
    }));
  };

  const handleStartSession = async () => {
    if (!selectedPiece) return;
    await start(selectedPiece.id);
  };

  if (repertoireLoading) return <p>Loading...</p>;

  return (
    <div
      style={{
        display: "grid",
        gap: 24,
        maxWidth: 400,
        margin: "0 auto",
        padding: 16,
      }}
    >
      <h1>Practice</h1>

      <PieceSelector
        pieces={pieces}
        selectedPiece={selectedPiece}
        onSelect={handlePieceSelected}
      />

      <PracticeModeSelector
        mode={config.mode}
        setMode={(mode) => setConfig((prev) => ({ ...prev, mode }))}
      />

      {config.mode === "passage" && (
        <PassageSelector
          startBar={config.startBar}
          endBar={config.endBar}
          setStartBar={(startBar) =>
            setConfig((prev) => ({ ...prev, startBar }))
          }
          setEndBar={(endBar) => setConfig((prev) => ({ ...prev, endBar }))}
        />
      )}

      <PracticeSettings
        tempo={config.tempo}
        setTempo={(tempo) => setConfig((prev) => ({ ...prev, tempo }))}
        countdown={config.countdown}
        setCountdown={(countdown) =>
          setConfig((prev) => ({ ...prev, countdown }))
        }
        metronome={config.metronome}
        setMetronome={(metronome) =>
          setConfig((prev) => ({ ...prev, metronome }))
        }
        tuner={config.tuner}
        setTuner={(tuner) => setConfig((prev) => ({ ...prev, tuner }))}
      />

      <StartPracticeButton
        disabled={!selectedPiece}
        loading={sessionLoading || status === "starting"}
        onClick={handleStartSession}
      />
    </div>
  );
}
