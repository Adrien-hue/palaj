import type { AgentDay, AgentPlanning } from "@/types";

function isAgentPlanning(x: unknown): x is AgentPlanning {
  if (!x || typeof x !== "object") return false;

  const p = x as Partial<AgentPlanning>;

  return (
    typeof p.start_date === "string" &&
    typeof p.end_date === "string" &&
    !!p.agent &&
    typeof (p.agent as any).id === "number" &&
    Array.isArray(p.days)
  );
}

function sortDays(days: AgentDay[]): AgentDay[] {
  return days.slice().sort((a, b) => a.day_date.localeCompare(b.day_date));
}

function upsertDay(days: AgentDay[], day: AgentDay): AgentDay[] {
  const idx = days.findIndex((d) => d.day_date === day.day_date);

  if (idx === -1) return sortDays([...days, day]);

  const copy = days.slice();
  copy[idx] = day;
  return copy;
}

export function optimisticApplyDayById(
  planning: AgentPlanning | undefined,
  args: {
    dayDate: string;
    day_type: string;
    description: string | null;
    tranche_id: number | null;
  }
): AgentPlanning | undefined {
  if (!planning) return planning;

  if (!isAgentPlanning(planning)) return planning;

  const existing = planning.days.find((d) => d.day_date === args.dayDate);

  const nextDay: AgentDay = existing
    ? {
        ...existing,
        day_type: args.day_type,
        description: args.description,
        tranches: args.tranche_id === null ? [] : existing.tranches,
      }
    : {
        day_date: args.dayDate,
        day_type: args.day_type,
        description: args.description,
        is_off_shift: false,
        tranches: [],
      };

  return {
    ...planning,
    days: upsertDay(planning.days, nextDay),
  };
}

export function applyServerDay(
  planning: AgentPlanning | undefined,
  serverDay: AgentDay
): AgentPlanning | undefined {
  if (!planning) return planning;
  if (!isAgentPlanning(planning)) return planning;

  return {
    ...planning,
    days: upsertDay(planning.days, serverDay),
  };
}

export function optimisticRemoveDay(
  planning: AgentPlanning | undefined,
  dayDate: string
): AgentPlanning | undefined {
  if (!planning) return planning;
  if (!isAgentPlanning(planning)) return planning;

  return {
    ...planning,
    days: planning.days.filter((d) => d.day_date !== dayDate),
  };
}
