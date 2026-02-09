import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";

import type { ListParams, ListResponse } from "@/types/api";
import type { CreatePosteBody, PatchPosteBody, Poste, PosteDetail } from "@/types";

export async function createPoste(body: CreatePosteBody) {
  return apiFetch<Poste>(backendPath(`/postes`), { method: "POST", body });
}

export async function getPoste(id: number) {
  return apiFetch<PosteDetail>(backendPath(`/postes/${id}`));
}

export async function listPostes(params: ListParams = {page: 1, page_size: 20}) {
  const search = new URLSearchParams();

  if (params.page != null) search.set("page", String(params.page));
  if (params.page_size != null) search.set("page_size", String(params.page_size));

  const qs = search.toString();
  return apiFetch<ListResponse<Poste>>(backendPath(`/postes${qs ? `?${qs}` : ""}`));
}

export async function patchPoste(id: number, body: PatchPosteBody) {
  return apiFetch<Poste>(backendPath(`/postes/${id}`), { method: "PATCH", body });
}

export async function removePoste(id: number) {
  return apiFetch<void>(backendPath(`/postes/${id}`), { method: "DELETE" });
}