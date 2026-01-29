import { Agent } from "./agent";
import { AgentDay } from "./agentDay";
import { Team } from "./team";

export type TeamAgentPlanning = {
  agent: Agent;
  days: AgentDay[];
};

export type TeamPlanning = {
  team: Team;
  start_date: string;
  end_date: string;
  days: string[];
  agents: TeamAgentPlanning[];
};