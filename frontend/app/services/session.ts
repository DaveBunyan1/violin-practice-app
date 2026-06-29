import { api } from "@/app/lib/api";
import { StartSessionRequest, StartSessionOutput } from "../types/session";

export async function startSession(request: StartSessionRequest) {
  return api.post<StartSessionOutput>("/session/start", request);
}
