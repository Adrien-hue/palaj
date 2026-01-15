import { apiFetch } from "@/lib/api";
import type { ListParams, ListResponse } from "@/types/api";
import type { Tranche, CreateTrancheBody, UpdateTrancheBody } from "@/types";

export async function createTranche(body: CreateTrancheBody): Promise<Tranche> {
  return apiFetch<Tranche>(`/tranches/`, { method: "POST", body });
}

export async function getTranche(trancheId: number): Promise<Tranche> {
  return apiFetch<Tranche>(`/tranches/${trancheId}`);
}

export async function listTranches(params: ListParams = { page: 1, page_size: 20 }) {
  const search = new URLSearchParams();
  if (params.page != null) search.set("page", String(params.page));
  if (params.page_size != null) search.set("page_size", String(params.page_size));

  const qs = search.toString();
  return apiFetch<ListResponse<Tranche>>(`/tranches${qs ? `?${qs}` : ""}`);
}

export async function listTranchesForPoste(posteId: number): Promise<Tranche[]> {
  return apiFetch<Tranche[]>(`/postes/${posteId}/tranches`);
}

export async function patchTranche(trancheId: number, body: UpdateTrancheBody): Promise<Tranche> {
  return apiFetch<Tranche>(`/tranches/${trancheId}`, { method: "PATCH", body });
}

export async function removeTranche(trancheId: number): Promise<void> {
  await apiFetch(`/tranches/${trancheId}`, { method: "DELETE" });
}
