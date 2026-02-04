// src/services/agent-planning.service.ts
import { apiFetch } from "@/lib/api";
import type { AgentDay, AgentDayPutDTO } from "@/types";

export async function putAgentDayPlanning(
  agentId: number,
  dayDate: string, // "YYYY-MM-DD"
  body: AgentDayPutDTO
) {
  return apiFetch<AgentDay>(
    `/agents/${agentId}/planning/days/${dayDate}`,
    {
      method: "PUT",
      body,
    }
  );
}

export async function deleteAgentDayPlanning(
  agentId: number,
  dayDate: string
) {
  return apiFetch<void>(
    `/agents/${agentId}/planning/days/${dayDate}`,
    {
      method: "DELETE",
    }
  );
}
