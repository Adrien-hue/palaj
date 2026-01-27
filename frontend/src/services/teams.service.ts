import { apiFetch } from "@/lib/api";
import type { ListParams, ListResponse } from "@/types/api";
import type { Team, CreateTeamBody, PatchTeamBody } from "@/types";

export async function createTeam(body: CreateTeamBody): Promise<Team> {
  return apiFetch("/teams/", { method: "POST", body });
}

export async function getTeam(teamId: number): Promise<Team> {
  return apiFetch<Team>(`/teams/${teamId}`);
}

export async function listTeams(params: ListParams = { page: 1, page_size: 20 }) {
  const search = new URLSearchParams();
  if (params.page != null) search.set("page", String(params.page));
  if (params.page_size != null) search.set("page_size", String(params.page_size));

  const qs = search.toString();
  return apiFetch<ListResponse<Team>>(`/teams${qs ? `?${qs}` : ""}`);
}

export async function updateTeam(teamId: number, body: PatchTeamBody): Promise<Team> {
  return apiFetch<Team>(`/teams/${teamId}`, { method: "PATCH", body });
}

export async function removeTeam(teamId: number): Promise<void> {
  await apiFetch(`/teams/${teamId}`, { method: "DELETE" });
}
