import { apiFetch } from "@/lib/api";
import { backendPath } from "@/lib/backendPath";

import { PosteCoverageDayDTO, PosteCoverageDto, PosteCoveragePutDto } from "@/types";

export async function getPosteCoverage(id: number) {
  return apiFetch<PosteCoverageDto>(backendPath(`/postes/${id}/coverage`));
}

export async function getPosteCoverageForDay(posteId: number, date: string) {
  console.log("FETCH coverage", date, posteId);
  return apiFetch<PosteCoverageDayDTO>(backendPath(`/postes/${posteId}/planning/coverage?date=${date}`));
}

export async function putPosteCoverage(id: number, payload: PosteCoveragePutDto) {
  return apiFetch<PosteCoverageDto>(backendPath(`/postes/${id}/coverage`), {
    method: "PUT",
    body: payload,
  });
}