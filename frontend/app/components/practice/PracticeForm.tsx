"use client";

import { Piece } from "../../types/Piece";
import PieceSelector from "./PieceSelector";
import PracticeModeSelector from "./PracticeModeSelector";
import PassageSelector from "./PassageSelector";
import PracticeSettings from "./PracticeSettings";
import StartPracticeButton from "./StartPracticeButton";

interface PracticeFormProps {
  pieces: Piece[];
  selectedPiece: Piece | null;
  config: any;
  sessionLoading: boolean;
  status: string;
  onPieceSelect: (piece: Piece) => void;
  onConfigChange: React.Dispatch<React.SetStateAction<any>>;
  onStartSession: () => void;
}

export default function PracticeForm({
  pieces,
  selectedPiece,
  config,
  sessionLoading,
  status,
  onPieceSelect,
  onConfigChange,
  onStartSession,
}: PracticeFormProps) {
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
      <h1>Practice Configuration</h1>

      <PieceSelector
        pieces={pieces}
        selectedPiece={selectedPiece}
        onSelect={onPieceSelect}
      />

      <PracticeModeSelector
        mode={config.mode}
        setMode={(mode) => onConfigChange((prev: any) => ({ ...prev, mode }))}
      />

      {config.mode === "passage" && (
        <PassageSelector
          startBar={config.startBar}
          endBar={config.endBar}
          setStartBar={(startBar) =>
            onConfigChange((prev: any) => ({ ...prev, startBar }))
          }
          setEndBar={(endBar) =>
            onConfigChange((prev: any) => ({ ...prev, endBar }))
          }
        />
      )}

      <PracticeSettings
        tempo={config.tempo}
        setTempo={(tempo) =>
          onConfigChange((prev: any) => ({ ...prev, tempo }))
        }
        countdown={config.countdown}
        setCountdown={(countdown) =>
          onConfigChange((prev: any) => ({ ...prev, countdown }))
        }
        metronome={config.metronome}
        setMetronome={(metronome) =>
          onConfigChange((prev: any) => ({ ...prev, metronome }))
        }
        tuner={config.tuner}
        setTuner={(tuner) =>
          onConfigChange((prev: any) => ({ ...prev, tuner }))
        }
      />

      <StartPracticeButton
        disabled={!selectedPiece}
        loading={sessionLoading || status === "starting"}
        onClick={onStartSession}
      />
    </div>
  );
}
