import { api } from "@/app/lib/api";
import { StartSessionRequest, StartSessionResponse } from "../types/session";

export async function startSession(request: StartSessionRequest) {
  return api.post<StartSessionResponse>("/session/start", request);
}
