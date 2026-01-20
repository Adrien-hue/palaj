"use client";

import { useMemo, useState, useEffect } from "react";
import type { AgentPlanningVm, AgentDayVm } from "@/features/planning/vm/planning.vm";
import { MonthDayCell } from "./MonthDayCell";
import { MonthDayDrawer } from "./MonthDayDrawer";
import { buildDaysRange, isInSameMonth } from "../utils/month.utils";
import { isoWeekRangeFrom } from "@/features/planning/utils/planning.utils";

export function MonthlyPlanningGrid({
  anchorMonth, // "YYYY-MM-DD" dans le mois
  planning,
  posteNameById,
}: {
  anchorMonth: string;
  planning: AgentPlanningVm;
  posteNameById: Map<number, string>;
}) {
  const [selected, setSelected] = useState<string | null>(null);

  const byDate = useMemo(
    () => new Map(planning.days.map((d) => [d.day_date, d])),
    [planning.days]
  );

  const allDates = useMemo(
    () => buildDaysRange(planning.start_date, planning.end_date),
    [planning.start_date, planning.end_date]
  );

  const selectedDay: AgentDayVm | null = selected ? byDate.get(selected) ?? null : null;
  const selectedWeek = selectedDay ? isoWeekRangeFrom(selectedDay.day_date) : null;

  // UX: Esc to close drawer (safe, small win)
  useEffect(() => {
    if (!selectedDay) return;

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setSelected(null);
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [selectedDay]);

  return (
    <section className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-5 shadow-sm">
      <div className="grid grid-cols-7 gap-3">
        {["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"].map((d) => (
          <div
            key={d}
            className="px-2 text-xs font-semibold text-[color:var(--app-muted)]"
          >
            {d}
          </div>
        ))}

        {allDates.map((date) => {
          const day = byDate.get(date)!; // normalisé => existe
          const outside = !isInSameMonth(date, anchorMonth);
          const isSelected = selected === date;
          const isWeek = selectedWeek
            ? date >= selectedWeek.start && date <= selectedWeek.end
            : false;

          return (
            <MonthDayCell
              key={date}
              day={day}
              isOutsideMonth={outside}
              isSelected={isSelected}
              isInSelectedWeek={isWeek}
              onSelect={() => setSelected(date)}
              posteNameById={posteNameById}
            />
          );
        })}
      </div>

      <MonthDayDrawer
        open={!!selectedDay}
        onClose={() => setSelected(null)}
        selectedDay={selectedDay}
        posteNameById={posteNameById}
      />
    </section>
  );
}
