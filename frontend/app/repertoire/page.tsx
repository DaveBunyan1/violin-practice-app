"use client";

import { useState } from "react";
import PieceCard from "../components/PieceCard";
import CreatePieceForm from "../components/repertoire/CreatePieceForm";
import { useRepertoire } from "../hooks/useRepertoire";

export default function RepertoirePage() {
  const { pieces, loading, refresh } = useRepertoire();
  const [showCreate, setShowCreate] = useState(false);

  if (loading) return <p>Loading...</p>;

  return (
    <div>
      <h1>Repertoire</h1>

      <button onClick={() => setShowCreate(true)}>Add Piece</button>

      {showCreate && (
        <CreatePieceForm
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            refresh();
          }}
        />
      )}

      {pieces.length > 0 ? (
        pieces.map((piece) => <PieceCard key={piece.id} piece={piece} />)
      ) : (
        <div>No Pieces Found</div>
      )}
    </div>
  );
}
