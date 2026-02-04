import { apiFetch } from "@/lib/api";

import { PosteCoverageDayDTO, PosteCoverageDto, PosteCoveragePutDto } from "@/types";

export async function getPosteCoverage(id: number) {
  return apiFetch<PosteCoverageDto>(`/postes/${id}/coverage`);
}

export async function getPosteCoverageForDay(posteId: number, date: string) {
  console.log("FETCH coverage", date, posteId);
  return apiFetch<PosteCoverageDayDTO>(`/postes/${posteId}/planning/coverage?date=${date}`);
}

export async function putPosteCoverage(id: number, payload: PosteCoveragePutDto) {
  return apiFetch<PosteCoverageDto>(`/postes/${id}/coverage`, {
    method: "PUT",
    body: payload,
  });
}