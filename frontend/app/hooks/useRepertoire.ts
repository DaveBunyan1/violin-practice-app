import { useEffect, useState } from "react";
import { getRepertoire } from "../services/repertoire";
import { Piece } from "../types/Piece";

export function useRepertoire() {
  const [pieces, setPieces] = useState<Piece[]>([]);
  const [selectedPiece, setSelectedPiece] = useState<Piece | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRepertoire()
      .then(setPieces)
      .finally(() => setLoading(false));
  }, []);

  const selectPiece = (piece: Piece) => {
    setSelectedPiece(piece);
  };

  return {
    pieces,
    selectedPiece,
    selectPiece,
    setSelectedPiece,
    loading,
  };
}
