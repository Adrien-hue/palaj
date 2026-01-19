import { apiFetch } from "@/lib/api";
import type { ListParams, ListResponse } from "@/types/api";
import type { Regime, RegimeDetail, CreateRegimeBody, UpdateRegimeBody } from "@/types";

export async function createRegime(body: CreateRegimeBody): Promise<Regime> {
  return apiFetch("/regimes/", { method: "POST", body });
}

export async function listRegimes(params: ListParams = { page: 1, page_size: 20 }) {
  const search = new URLSearchParams();
  if (params.page != null) search.set("page", String(params.page));
  if (params.page_size != null) search.set("page_size", String(params.page_size));

  const qs = search.toString();
  return apiFetch<ListResponse<Regime>>(`/regimes${qs ? `?${qs}` : ""}`);
}

export async function getRegime(regimeId: number): Promise<RegimeDetail> {
  return apiFetch<RegimeDetail>(`/regimes/${regimeId}`);
}

export async function updateRegime(regimeId: number, body: UpdateRegimeBody): Promise<Regime> {
  return apiFetch<Regime>(`/regimes/${regimeId}`, { method: "PATCH", body });
}

export async function removeRegime(regimeId: number): Promise<void> {
  await apiFetch(`/regimes/${regimeId}`, { method: "DELETE" });
}
