"use client";

import { Piece } from "@/app/types/Piece";

interface PieceSelectorProps {
  pieces: Piece[];
  selectedPiece: Piece | null;
  onSelect: (piece: Piece) => void;
}

export default function PieceSelector({
  pieces,
  selectedPiece,
  onSelect,
}: PieceSelectorProps) {
  const handleChange = (id: number) => {
    const piece = pieces.find((p) => p.id === id);

    if (piece) {
      onSelect(piece);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <label style={{ fontWeight: "bold" }}>Piece</label>

      <select
        value={selectedPiece?.id ?? ""}
        onChange={(e) => handleChange(Number(e.target.value))}
        style={{ padding: 8, borderRadius: 4 }}
      >
        <option value="" disabled>
          Choose a piece
        </option>

        {pieces.map((piece) => (
          <option key={piece.id} value={piece.id}>
            {piece.title}
          </option>
        ))}
      </select>
    </div>
  );
}
