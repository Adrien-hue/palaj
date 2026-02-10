import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";

import type {
  TeamPlanningBulkPutBody,
  TeamPlanningDayBulkPutResponseDTO,
} from "@/types";

export async function bulkUpsertTeamPlanningDays(
  teamId: number,
  body: TeamPlanningBulkPutBody,
): Promise<TeamPlanningDayBulkPutResponseDTO> {
  return apiFetch<TeamPlanningDayBulkPutResponseDTO>(
    backendPath(`/teams/${teamId}/planning/days:bulk`),
    { method: "PUT", body },
  );
}
