import { apiFetch } from "@/lib/api";

import type { AgentPlanning } from "@/types";

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
