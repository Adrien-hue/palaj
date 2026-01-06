import type { AgentPlanning, Tranche } from "@/types";
import type { AgentPlanningVm, AgentDayVm, ShiftSegmentVm } from "./planning.vm";
import { addDaysISO, parseTimeToMinutes } from "../utils/planning.utils";

function emptyDay(day_date: string): AgentDayVm {
  return {
    day_date,
    day_type: "unknown",
    description: null,
    is_off_shift: false,
    segments: [],
  };
}

function splitOvernight(dayDate: string, t: Tranche): Array<{ day_date: string; seg: ShiftSegmentVm }> {
  const startMin = parseTimeToMinutes(t.heure_debut);
  const endMin = parseTimeToMinutes(t.heure_fin);

  if (endMin >= startMin) {
    return [{
      day_date: dayDate,
      seg: {
        key: `${dayDate}-${t.id}-${t.heure_debut}`,
        sourceTrancheId: t.id,
        nom: t.nom,
        posteId: t.poste_id,
        start: t.heure_debut,
        end: t.heure_fin,
        continuesPrev: false,
        continuesNext: false,
      },
    }];
  }

  const nextDay = addDaysISO(dayDate, 1);

  return [
    {
      day_date: dayDate,
      seg: {
        key: `${dayDate}-${t.id}-p1`,
        sourceTrancheId: t.id,
        nom: t.nom,
        posteId: t.poste_id,
        start: t.heure_debut,
        end: "23:59:00",
        continuesPrev: false,
        continuesNext: true,
      },
    },
    {
      day_date: nextDay,
      seg: {
        key: `${nextDay}-${t.id}-p2`,
        sourceTrancheId: t.id,
        nom: t.nom,
        posteId: t.poste_id,
        start: "00:00:00",
        end: t.heure_fin,
        continuesPrev: true,
        continuesNext: false,
      },
    },
  ];
}

export function buildPlanningVm(dto: AgentPlanning): AgentPlanningVm {
  // 1) map date -> day dto (pour type/desc/off_shift)
  const dayByDate = new Map(dto.days.map((d) => [d.day_date, d]));

  // 2) initialise la plage complète
  const daysVm: AgentDayVm[] = [];
  let cur = dto.start_date;
  while (cur <= dto.end_date) {
    const dayDto = dayByDate.get(cur);
    daysVm.push(
      dayDto
        ? { ...dayDto, segments: [] }
        : emptyDay(cur)
    );
    cur = addDaysISO(cur, 1);
  }

  const segByDate = new Map(daysVm.map((d) => [d.day_date, d.segments]));

  // 3) split + distribution des segments
  for (const dayDto of dto.days) {
    for (const t of dayDto.tranches) {
      for (const part of splitOvernight(dayDto.day_date, t)) {
        if (!segByDate.has(part.day_date)) continue; // hors range (rare)
        segByDate.get(part.day_date)!.push(part.seg);
      }
    }
  }

  // 4) tri des segments dans chaque jour
  for (const d of daysVm) {
    d.segments.sort((a, b) => a.start.localeCompare(b.start));
  }

  return {
    agent: dto.agent,
    start_date: dto.start_date,
    end_date: dto.end_date,
    days: daysVm,
  };
}
