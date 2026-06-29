import { useState } from "react";
import { PracticeConfig } from "../types/PracticeConfig";

export function usePracticeConfig() {
  const [config, setConfig] = useState<PracticeConfig>({
    mode: "full",
    startBar: 1,
    endBar: 1,
    tempo: 80,
    countdown: 3,
    metronome: true,
    tuner: false,
  });

  return { config, setConfig };
}
