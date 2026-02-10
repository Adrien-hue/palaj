import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";

import type { AgentTeam } from "@/types";

export async function searchAgentTeams(params: {
  agent_id?: number;
  team_id?: number;
}): Promise<AgentTeam[]> {
  const search = new URLSearchParams();
  if (params.agent_id != null) search.set("agent_id", String(params.agent_id));
  if (params.team_id != null) search.set("team_id", String(params.team_id));

  const qs = search.toString();
  return apiFetch<AgentTeam[]>(backendPath(`/agent-teams${qs ? `?${qs}` : ""}`));
}

export async function addAgentToTeam(agentId: number, teamId: number): Promise<void> {
  await apiFetch(backendPath(`/agent-teams/${agentId}/${teamId}`), { method: "POST" });
}

export async function removeAgentFromTeam(agentId: number, teamId: number): Promise<void> {
  await apiFetch(backendPath(`/agent-teams/${agentId}/${teamId}`), { method: "DELETE" });
}
