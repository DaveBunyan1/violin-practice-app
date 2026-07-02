"use client";

import { useState } from "react";
import PieceCard from "../components/PieceCard";
import CreatePieceForm from "../components/repertoire/CreatePieceForm";
import { NoteStudio } from "../components/repertoire/NoteStudio";
import { useRepertoire } from "../hooks/useRepertoire";
import { updatePieceNotes } from "../services/repertoire";
import { Piece, PieceNote } from "../types/Piece";

export default function RepertoirePage() {
  const { pieces, loading, refresh } = useRepertoire();
  const [showCreate, setShowCreate] = useState(false);

  const [editingPiece, setEditingPiece] = useState<Piece | null>(null);

  const handleSaveNotesMatrix = async (notesPayload: PieceNote[]) => {
    if (!editingPiece) return;

    try {
      await updatePieceNotes(editingPiece.id, notesPayload);
      setEditingPiece(null); // Close the studio overlay
      refresh(); // Re-fetch from FastAPI to update the PieceCard duration strings!
    } catch (err) {
      console.error(err);
      alert("Failed to sync structural composition records.");
    }
  };

  if (loading) return <p>Loading...</p>;

  return (
    <div style={{ padding: "20px", fontFamily: "sans-serif" }}>
      <h1>Repertoire</h1>

      <button
        onClick={() => setShowCreate(true)}
        style={{ marginBottom: "20px" }}
      >
        Add Piece
      </button>

      {showCreate && (
        <CreatePieceForm
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            refresh();
          }}
        />
      )}

      {editingPiece && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 1000,
          }}
        >
          <div
            style={{
              backgroundColor: "#222",
              padding: "24px",
              borderRadius: "8px",
              width: "90%",
              maxWidth: "800px",
              maxHeight: "90vh",
              overflowY: "auto",
            }}
          >
            <button
              onClick={() => setEditingPiece(null)}
              style={{ float: "right", cursor: "pointer" }}
            >
              ✕ Close
            </button>
            <NoteStudio
              selectedPiece={editingPiece}
              onSaveNotes={handleSaveNotesMatrix}
            />
          </div>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {pieces.length > 0 ? (
          pieces.map((piece) => (
            <div
              key={piece.id}
              style={{
                border: "1px solid #eaeaea",
                borderRadius: "8px",
                padding: "16px",
                background: "#222",
              }}
            >
              <PieceCard key={piece.id} piece={piece} />

              <button
                onClick={() => setEditingPiece(piece as Piece)}
                style={{
                  marginTop: "12px",
                  padding: "6px 14px",
                  background: "#0070f3",
                  color: "#fff",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                📝 Edit Notes Timeline
              </button>
            </div>
          ))
        ) : (
          <div>No Pieces Found</div>
        )}
      </div>
    </div>
  );
}
