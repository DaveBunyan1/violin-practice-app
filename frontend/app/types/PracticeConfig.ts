export type PracticeConfig = {
  mode: "full" | "passage";
  startBar: number;
  endBar: number;
  tempo: number;
  countdown: number;
  metronome: boolean;
  tuner: boolean;
};

export type PracticeConfigUpdate = Partial<PracticeConfig>;
