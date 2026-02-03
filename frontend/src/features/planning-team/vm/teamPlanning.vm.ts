import { AgentDay, TeamPlanning } from "@/types";

export type TeamPlanningVm = {
  team: TeamPlanning["team"];
  start_date: string;
  end_date: string;
  days: string[];
  rows: Array<{
    agent: TeamPlanning["agents"][number]["agent"];
    days: Array<AgentDay>;
  }>;
};
