import { apiFetch } from "@/lib/api";
import type { ListParams, ListResponse } from "@/types/api";
import type { Agent } from "@/types";

export type ListAgentsParams = {
  page?: number;
  page_size?: number;
};

export async function listAgents(params: ListParams = {page: 1, page_size: 20}) {
  const search = new URLSearchParams();

  if (params.page != null) search.set("page", String(params.page));
  if (params.page_size != null) search.set("page_size", String(params.page_size));

  const qs = search.toString();
  return apiFetch<ListResponse<Agent>>(`/agents${qs ? `?${qs}` : ""}`);
}
