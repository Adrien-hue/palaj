import type { Agent, AgentDay, AgentPlanning } from "@/types";

export type ShiftSegmentVm = {
  key: string;
  sourceTrancheId: number;

  nom: string;
  posteId: number;

  start: string; // "HH:MM:SS"
  end: string;   // "HH:MM:SS"

  continuesPrev: boolean;
  continuesNext: boolean;

  color: string | null;
};

export type AgentDayVm = Omit<AgentDay, "tranches"> & {
  segments: ShiftSegmentVm[];
};

export type AgentPlanningVm = Omit<AgentPlanning, "days"> & {
  agent: Agent;
  days: AgentDayVm[];
};
