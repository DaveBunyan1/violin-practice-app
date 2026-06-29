import { useEffect, useState } from "react";
import { getRepertoire } from "../services/repertoire";
import { Piece } from "../types/Piece";

export function useRepertoire() {
  const [pieces, setPieces] = useState<Piece[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRepertoire()
      .then(setPieces)
      .finally(() => setLoading(false));
  }, []);

  return { pieces, loading };
}
