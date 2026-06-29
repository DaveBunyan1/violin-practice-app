import { Piece } from "../types/Piece";

type Props = {
  piece: Piece;
};

export default function PieceCard({ piece }: Props) {
  return (
    <div>
      <h3>{piece.title}</h3>

      <p>Duration: {piece.total_duration.toFixed(1)}s</p>

      <p>Notes: {piece.notes.length}s</p>

      <button>Practice</button>
    </div>
  );
}
