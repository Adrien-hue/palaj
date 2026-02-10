import { apiFetch } from "@/lib/api/universal";
import type { ActionResponse } from "@/types/common";

export function logout() {
  return apiFetch<ActionResponse>("/auth/logout", { method: "POST" });
}

export function logoutAll() {
  return apiFetch<ActionResponse>("/auth/logout-all", { method: "POST" });
}
