// src/services/agent-planning.service.ts
import { apiFetch } from "@/lib/api";
import type { AgentDay, AgentDayPutDTO, AgentPlanningDayBulkPutDTO, AgentPlanningDayBulkPutResponseDTO, AgentPlanningDayBatchBody, AgentPlanningDayBatchResponse } from "@/types";

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

export async function bulkUpsertAgentPlanningDays(
  agentId: number,
  payload: AgentPlanningDayBulkPutDTO,
): Promise<AgentPlanningDayBulkPutResponseDTO> {
  return apiFetch<AgentPlanningDayBulkPutResponseDTO>(
    `/agents/${agentId}/planning/days:bulk`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: payload,
    },
  );
}

export async function postAgentPlanningDayBatch(body: AgentPlanningDayBatchBody) {
  return apiFetch<AgentPlanningDayBatchResponse>(
    `/agents/planning/days/batch`,
    { method: "POST", body }
  );
}