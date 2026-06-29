export type Piece = {
  id: number;
  title: string;
  total_duration: number;
  bpm: number;
  time_signature_numerator: number;
  notes: PieceNote[];
};

export type PieceNote = {
  note: string;
  time: number;
  duration: number;
};
