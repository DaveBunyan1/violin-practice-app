"use client";

import { useState } from "react";
import { createPiece } from "../../services/repertoire";
import { CreatePieceInput } from "../../types/CreatePiece";

type Props = {
  onClose: () => void;
  onCreated: () => void;
};

export default function CreatePieceForm({ onClose, onCreated }: Props) {
  const [form, setForm] = useState<CreatePieceInput>({
    title: "",
    bpm: 80,
    time_signature_numerator: 4,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const update = <K extends keyof CreatePieceInput>(
    key: K,
    value: CreatePieceInput[K],
  ) => {
    setForm((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      await createPiece(form);
      onCreated();
    } catch (err: any) {
      setError(err.message || "Failed to create piece");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ border: "1px solid #333", padding: 16, borderRadius: 8 }}>
      <h2>Create Piece</h2>

      {/* TITLE */}
      <div style={{ marginBottom: 12 }}>
        <label>Title</label>
        <input
          value={form.title}
          onChange={(e) => update("title", e.target.value)}
          style={{ width: "100%" }}
        />
      </div>

      {/* BPM */}
      <div style={{ marginBottom: 12 }}>
        <label>BPM</label>
        <input
          type="number"
          value={form.bpm}
          onChange={(e) => update("bpm", Number(e.target.value))}
          style={{ width: "100%" }}
        />
      </div>

      {/* TIME SIGNATURE */}
      <div style={{ marginBottom: 12 }}>
        <label>Time Signature</label>
        <input
          type="number"
          value={form.time_signature_numerator}
          onChange={(e) =>
            update("time_signature_numerator", Number(e.target.value))
          }
          style={{ width: "100%" }}
        />
      </div>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={handleSubmit} disabled={loading}>
          {loading ? "Creating..." : "Create"}
        </button>

        <button onClick={onClose}>Cancel</button>
      </div>
    </div>
  );
}
