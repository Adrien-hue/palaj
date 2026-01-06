import { Agent } from "./agent";
import { AgentDay } from "./agentDay";

export type AgentPlanning = {
  agent: Agent;
  start_date: string;
  end_date: string;
  days: AgentDay[];
};