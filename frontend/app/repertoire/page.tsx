"use client";

import PieceCard from "../components/PieceCard";
import { useRepertoire } from "../hooks/useRepertoire";

export default function RepertoirePage() {
  const { pieces, loading } = useRepertoire();

  if (loading) {
    return <p>Loading...</p>;
  }

  return (
    <>
      <h1>Repertoire</h1>

      <button>Add Piece</button>

      {pieces.map((piece) => (
        <PieceCard key={piece.id} piece={piece} />
      ))}
    </>
  );
}
