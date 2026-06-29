import { useEffect, useState } from "react";
import { getRepertoire } from "../services/repertoire";
import { Piece } from "../types/Piece";

export function useRepertoire() {
  const [pieces, setPieces] = useState<Piece[]>([]);
  const [selectedPiece, setSelectedPiece] = useState<Piece | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await getRepertoire();
      setPieces(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
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
    refresh: load,
  };
}
