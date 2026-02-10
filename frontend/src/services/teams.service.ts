import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";

import type { ListParams, ListResponse } from "@/types/api";
import type { Team, CreateTeamBody, PatchTeamBody } from "@/types";

export async function createTeam(body: CreateTeamBody): Promise<Team> {
  return apiFetch(backendPath(`/teams`), { method: "POST", body });
}

export async function getTeam(teamId: number): Promise<Team> {
  return apiFetch<Team>(backendPath(`/teams/${teamId}`));
}

export async function listTeams(params: ListParams = { page: 1, page_size: 20 }) {
  const search = new URLSearchParams();
  if (params.page != null) search.set("page", String(params.page));
  if (params.page_size != null) search.set("page_size", String(params.page_size));

  const qs = search.toString();
  return apiFetch<ListResponse<Team>>(backendPath(`/teams${qs ? `?${qs}` : ""}`));
}

export async function updateTeam(teamId: number, body: PatchTeamBody): Promise<Team> {
  return apiFetch<Team>(backendPath(`/teams/${teamId}`), { method: "PATCH", body });
}

export async function removeTeam(teamId: number): Promise<void> {
  await apiFetch(backendPath(`/teams/${teamId}`), { method: "DELETE" });
}
