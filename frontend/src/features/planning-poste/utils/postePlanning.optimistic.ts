// frontend/src/features/planning-poste/optimistic/postePlanning.optimistic.ts
import type {PostePlanningDayPutBody, PostePlanningDay, PostePlanning } from "@/types"; // ajuste tes imports

function isPostePlanning(x: unknown): x is PostePlanning {
  if (!x || typeof x !== "object") return false;

  const p = x as Partial<PostePlanning>;

  return (
    typeof p.start_date === "string" &&
    typeof p.end_date === "string" &&
    !!p.poste &&
    typeof (p.poste as any).id === "number" &&
    Array.isArray(p.days)
  );
}

function sortDays(days: PostePlanningDay[]): PostePlanningDay[] {
  return days.slice().sort((a, b) => a.day_date.localeCompare(b.day_date));
}

function upsertDay(days: PostePlanningDay[], day: PostePlanningDay): PostePlanningDay[] {
  const idx = days.findIndex((d) => d.day_date === day.day_date);

  if (idx === -1) return sortDays([...days, day]);

  const copy = days.slice();
  copy[idx] = day;
  return copy;
}

function upsertTranche(
  day: PostePlanningDay,
  trancheId: number,
  agentIds: number[]
): PostePlanningDay {
  const existingIdx = day.tranches.findIndex((t) => t.tranche.id === trancheId);

  const existing = existingIdx === -1 ? null : day.tranches[existingIdx];

  // on tente de conserver les agents existants (nom/prenom) quand possible
  const agents =
    existing?.agents?.length
      ? agentIds.map((id) => existing.agents.find((a) => a.id === id) ?? stubAgent(id))
      : agentIds.map(stubAgent);

  const nextTrancheBlock = {
    tranche: existing?.tranche ?? stubTranche(trancheId, day),
    agents,
  };

  if (existingIdx === -1) {
    return { ...day, tranches: [...day.tranches, nextTrancheBlock] };
  }

  const tranches = day.tranches.slice();
  tranches[existingIdx] = nextTrancheBlock;
  return { ...day, tranches };
}

function stubAgent(id: number) {
  return {
    id,
    nom: "",
    prenom: "",
    code_personnel: "",
    actif: true,
  };
}

function stubTranche(trancheId: number, day: PostePlanningDay) {
  // on ne connaît pas poste_id/nom/couleur sans cache -> stub
  return {
    id: trancheId,
    poste_id: 0,
    nom: "",
    heure_debut: "00:00:00",
    heure_fin: "00:00:00",
    color: null,
  };
}

export function optimisticApplyPostePlanningDay(
  planning: PostePlanning | undefined,
  args: {
    dayDate: string;
    day_type: string;
    description: string | null;
    body: PostePlanningDayPutBody;
  }
): PostePlanning | undefined {
  if (!planning) return planning;
  if (!isPostePlanning(planning)) return planning;

  const existing = planning.days.find((d) => d.day_date === args.dayDate);

  // base : soit existing, soit nouveau jour vide
  let nextDay: PostePlanningDay = existing
    ? {
        ...existing,
        day_type: args.day_type,
        description: args.description,
      }
    : {
        day_date: args.dayDate,
        day_type: args.day_type,
        description: args.description,
        is_off_shift: false,
        tranches: [],
      };

  // appliquer le body tranches -> met à jour tranches/agents
  // et si une tranche disparaît du body, on la retire (car le PUT représente l'état cible)
  const wantedTrancheIds = new Set(args.body.tranches.map((t) => t.tranche_id));

  nextDay = {
    ...nextDay,
    tranches: nextDay.tranches.filter((t) => wantedTrancheIds.has(t.tranche.id)),
  };

  for (const t of args.body.tranches) {
    nextDay = upsertTranche(nextDay, t.tranche_id, t.agent_ids);
  }

  return {
    ...planning,
    days: upsertDay(planning.days, nextDay),
  };
}

export function applyServerDay(
  planning: PostePlanning | undefined,
  serverDay: PostePlanningDay
): PostePlanning | undefined {
  if (!planning) return planning;
  if (!isPostePlanning(planning)) return planning;

  return {
    ...planning,
    days: upsertDay(planning.days, serverDay),
  };
}

export function optimisticRemoveDay(
  planning: PostePlanning | undefined,
  dayDate: string
): PostePlanning | undefined {
  if (!planning) return planning;
  if (!isPostePlanning(planning)) return planning;

  return {
    ...planning,
    days: planning.days.filter((d) => d.day_date !== dayDate),
  };
}
