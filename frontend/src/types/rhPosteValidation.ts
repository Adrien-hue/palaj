import type { RhViolation } from "./rhValidation";

export type RhProfile = "fast" | "full";

export type RhRisk = "none" | "low" | "medium" | "high";
export type TriggerSeverity = "info" | "warning" | "error";

export type RhTriggerStat = {
  key: string;
  severity: TriggerSeverity;
  count: number;
};

export type RhDaySummary = {
  date: string;
  risk: RhRisk;
  agents_with_issues_count: number;
  agents_with_blockers_count: number;
  top_triggers: RhTriggerStat[];
};

export type RhPosteSummaryResponse = {
  poste_id: number;
  date_debut: string;
  date_fin: string;
  profile: RhProfile;
  eligible_agents_count: number;
  days: RhDaySummary[];
};

export type RhPosteSummaryVm = {
  posteId: number;
  range: { startISO: string; endISO: string };
  profile: RhProfile;
  eligibleAgentsCount: number;
  byDate: Record<string, RhDaySummary>;
};

export type RhPosteSummaryRequest = {
  poste_id: number;
  date_debut: string;
  date_fin: string;
};

export type RhPosteDayAgent = {
  agent_id: number;
  is_valid: boolean;
  errors_count: number;
  warnings_count: number;
  infos_count: number;
  violations: RhViolation[];
};

export type RhPosteDayResponse = {
  poste_id: number;
  date: string;
  profile: RhProfile;
  eligible_agents_count: number;
  agents: RhPosteDayAgent[];
};

export type RhPosteDayRequest = {
  poste_id: number;
  day: string;
  date_debut: string;
  date_fin: string;
};
