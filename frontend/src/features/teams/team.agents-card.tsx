"use client";

import type { Agent, AgentTeam, Team } from "@/types";
import { AssociationCard } from "@/features/memberships/AssociationCard";

import { searchAgentTeams, addAgentToTeam, removeAgentFromTeam } from "@/services/agent-teams.service";
import { listAgents } from "@/services/agents.service";

async function fetchAllAgents() {
  const pageSize = 200;
  let page = 1;
  const all: Agent[] = [];

  while (true) {
    const res = await listAgents({ page, page_size: pageSize });
    all.push(...res.items);
    if (res.items.length < pageSize) break;
    page += 1;
  }
  return all;
}

function agentLabel(a: Agent) {
  // adapte si besoin selon tes champs
  return `${a.nom} ${a.prenom}`.trim();
}

export function TeamAgentsCard({ team }: { team: Team }) {
  return (
    <AssociationCard<Agent, AgentTeam>
      title="Agents"
      entityName={`équipe "${team.name}"`}
      emptyText={`Aucun agent associé à cette équipe. Utilise "Ajouter" pour en associer un.`}
      loadAllItems={fetchAllAgents}
      searchLinks={() => searchAgentTeams({ team_id: team.id })}
      getItemId={(a) => a.id}
      getItemLabel={(a) => agentLabel(a) || `Agent #${a.id}`}
      getLinkItemId={(l) => l.agent_id}
      addLink={(agentId) => addAgentToTeam(agentId, team.id)}
      removeLink={(agentId) => removeAgentFromTeam(agentId, team.id)}
    />
  );
}
