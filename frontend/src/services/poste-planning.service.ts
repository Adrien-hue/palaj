import { apiFetch } from "@/lib/api";
import { backendPath } from "@/lib/backendPath";

import type { PostePlanningDay, PostePlanningDayPutBody } from "@/types";

export async function putPostePlanningDay(
  posteId: number,
  dayDate: string, // "YYYY-MM-DD"
  body: PostePlanningDayPutBody
) {
  return apiFetch<PostePlanningDay>(
    backendPath(`/postes/${posteId}/planning/days/${dayDate}`),
    {
      method: "PUT",
      body,
    }
  );
}

export async function deletePostePlanningDay(
  posteId: number,
  dayDate: string
) {
  return apiFetch<void>(
    backendPath(`/postes/${posteId}/planning/days/${dayDate}`),
    {
      method: "DELETE",
    }
  );
}