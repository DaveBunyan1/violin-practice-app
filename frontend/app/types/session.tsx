export type StartSessionRequest = {
  piece_id: number;
  start_bar: number | null;
  end_bar: number | null;
  target_bpm: number;
};

export type StartSessionOutput = {
  message: string;
  session_active: boolean;
};
