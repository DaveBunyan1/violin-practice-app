import { api } from "../lib/api";
import { Piece } from "../types/Piece";

// READ
export async function getRepertoire(): Promise<Piece[]> {
  return api.get<Piece[]>("/repertoire");
}

export async function getActivePiece(): Promise<Piece> {
  return api.get<Piece>("/repertoire/active");
}

export async function getPiece(id: number): Promise<Piece> {
  return api.get<Piece>(`/repertoire/${id}`);
}

// WRITE
export async function createPiece(piece: Partial<Piece>): Promise<Piece> {
  return api.post<Piece>("/repertoire", piece);
}

export async function updatePiece(
  id: number,
  piece: Partial<Piece>,
): Promise<Piece> {
  return api.put<Piece>(`/repertoire/${id}`, piece);
}

export async function deletePiece(id: number): Promise<void> {
  return api.del<void>(`/repertoire/${id}`);
}

export async function setActivePiece(id: number): Promise<void> {
  return api.post<void>(`/repertoire/${id}/activate`);
}
