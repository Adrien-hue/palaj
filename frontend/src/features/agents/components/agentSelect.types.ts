import type { DayType } from "@/components/planning/DayTypeBadge";

type NonWorkingDayType = Exclude<DayType, "working">;

export type AgentSelectStatus =
  | { dayType: NonWorkingDayType }
  | { dayType: "working"; trancheLabel?: string; trancheColor?: string | null };

export type AgentSelectStatusById = Map<number, AgentSelectStatus>;