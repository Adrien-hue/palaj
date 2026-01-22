import { apiFetch } from "@/lib/api";

import type { AgentPlanning, PostePlanning } from "@/types";

export async function getAgentPlanning(
  agentId: number,
  params: {
    startDate: string; // YYYY-MM-DD
    endDate: string; // YYYY-MM-DD
  }
) {
  const searchParams = new URLSearchParams();

  searchParams.set("start_date", params.startDate);
  searchParams.set("end_date", params.endDate);

  const qs = searchParams.toString();

  return apiFetch<AgentPlanning>(`agents/${agentId}/planning?${qs}`);
}

export async function getPostePlanning(
  posteId: number,
  params: { startDate: string; endDate: string }
) {
  const search = new URLSearchParams();
  search.set("start_date", params.startDate);
  search.set("end_date", params.endDate);

  return apiFetch<PostePlanning>(`/postes/${posteId}/planning?${search.toString()}`);
}