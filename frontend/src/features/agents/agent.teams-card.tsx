"use client";

import type { Agent, AgentTeam, Team } from "@/types";
import { AssociationCard } from "@/features/memberships/AssociationCard";

import {
  searchAgentTeams,
  addAgentToTeam,
  removeAgentFromTeam,
} from "@/services/agent-teams.service";
import { listTeams } from "@/services/teams.service";

async function fetchAllTeams() {
  const pageSize = 200;
  let page = 1;
  const all: Team[] = [];

  while (true) {
    const res = await listTeams({ page, page_size: pageSize });
    all.push(...res.items);
    if (res.items.length < pageSize) break;
    page += 1;
  }
  return all;
}

export function AgentTeamsCard({ agent }: { agent: Agent }) {
  const agentName =
    `${agent.nom} ${agent.prenom}`.trim() || `Agent #${agent.id}`;

  return (
    <AssociationCard<Team, AgentTeam>
      title="Équipes"
      entityName={`agent "${agentName}"`}
      emptyText={`Aucune équipe associée à cet agent. Utilise "Ajouter" pour en associer une.`}
      loadAllItems={fetchAllTeams}
      searchLinks={() => searchAgentTeams({ agent_id: agent.id })}
      getItemId={(t) => t.id}
      getItemLabel={(t) => t.name}
      getLinkItemId={(l) => l.team_id}
      addLink={(teamId) => addAgentToTeam(agent.id, teamId)}
      removeLink={(teamId) => removeAgentFromTeam(agent.id, teamId)}
    />
  );
}
