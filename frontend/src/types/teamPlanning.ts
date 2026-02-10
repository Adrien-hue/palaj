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

export type TeamPlanningBulkItem = {
  agent_id: number;
  day_dates: string[];
};

export type TeamPlanningBulkPutBody = {
  items: TeamPlanningBulkItem[];
  day_type: string;
  description: string | null;
  tranche_id: number | null;
};


export type TeamBulkUpdatedItem = {
  agent_id: number;
  planning_day: AgentDay;
};

export type TeamBulkFailedItem = {
  agent_id: number;
  day_date: string;
  code: string;
  message: string;
};

export type TeamPlanningDayBulkPutResponseDTO = {
  updated: TeamBulkUpdatedItem[];
  failed: TeamBulkFailedItem[];
};