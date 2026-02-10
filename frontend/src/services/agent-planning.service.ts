import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";
import type {
  AgentDay,
  AgentDayPutDTO,
  AgentPlanningDayBulkPutDTO,
  AgentPlanningDayBulkPutResponseDTO,
  AgentPlanningDayBatchBody,
  AgentPlanningDayBatchResponse,
} from "@/types";

export async function putAgentDayPlanning(
  agentId: number,
  dayDate: string, // "YYYY-MM-DD"
  body: AgentDayPutDTO
) {
  return apiFetch<AgentDay>(backendPath(`/agents/${agentId}/planning/days/${dayDate}`), {
    method: "PUT",
    body,
  });
}

export async function deleteAgentDayPlanning(agentId: number, dayDate: string) {
  return apiFetch<void>(backendPath(`/agents/${agentId}/planning/days/${dayDate}`), {
    method: "DELETE",
  });
}

export async function bulkUpsertAgentPlanningDays(
  agentId: number,
  payload: AgentPlanningDayBulkPutDTO
): Promise<AgentPlanningDayBulkPutResponseDTO> {
  return apiFetch<AgentPlanningDayBulkPutResponseDTO>(
    backendPath(`/agents/${agentId}/planning/days:bulk`),
    {
      method: "PUT",
      body: payload,
    }
  );
}

export async function postAgentPlanningDayBatch(body: AgentPlanningDayBatchBody) {
  return apiFetch<AgentPlanningDayBatchResponse>(backendPath(`/agents/planning/days/batch`), {
    method: "POST",
    body,
  });
}
