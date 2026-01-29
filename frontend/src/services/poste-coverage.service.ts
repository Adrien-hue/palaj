import { apiFetch } from "@/lib/api";

import { PosteCoverageDto, PosteCoveragePutDto } from "@/types";

export async function getPosteCoverage(id: number) {
  return apiFetch<PosteCoverageDto>(`/postes/${id}/coverage`);
}

export async function putPosteCoverage(id: number, payload: PosteCoveragePutDto) {
  return apiFetch<PosteCoverageDto>(`/postes/${id}/coverage`, {
    method: "PUT",
    body: payload,
  });
}