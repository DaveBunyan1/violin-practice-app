export type StartSessionRequest = {
  piece_id: number;
  start_bar: number | null;
  end_bar: number | null;
  target_bpm: number;
  countdownSeconds: number;
};

export type StartSessionOutput = {
  message: string;
  session_active: boolean;
};

export type SessionStatus =
  | "idle"
  | "starting"
  | "active"
  | "ending"
  | "ended"
  | "error";

export type PracticeSession = {
  sessionId?: number;
  status: SessionStatus;
  startedAt?: number;
  endedAt?: number;
};
