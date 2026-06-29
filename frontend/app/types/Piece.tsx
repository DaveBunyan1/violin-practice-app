export type Piece = {
  id: number;
  title: string;
  total_duration: number;
  notes: {
    note: string;
    time: number;
    duration: number;
  }[];
};
