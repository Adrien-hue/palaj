"use client";

import { useEffect, useMemo, useState } from "react";

import type { PostePlanningVm, PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";

import { buildDaysRange, isInSameMonth } from "@/features/planning/utils/month.utils";
import { isoWeekRangeFrom } from "@/features/planning/utils/planning.utils";

import { PosteDayCell } from "./PosteDayCell";
import { PosteDaySheet } from "./PosteDaySheet";

const DAYS = [
  { short: "Lun", full: "Lundi" },
  { short: "Mar", full: "Mardi" },
  { short: "Mer", full: "Mercredi" },
  { short: "Jeu", full: "Jeudi" },
  { short: "Ven", full: "Vendredi" },
  { short: "Sam", full: "Samedi" },
  { short: "Dim", full: "Dimanche" },
];

export function MonthlyPlanningGrid({
  anchorMonth,
  planning,
}: {
  anchorMonth: string;
  planning: PostePlanningVm;
}) {
  const [selected, setSelected] = useState<string | null>(null);

  const byDate = useMemo(
    () => new Map(planning.days.map((d) => [d.day_date, d] as const)),
    [planning.days]
  );

  const allDates = useMemo(
    () => buildDaysRange(planning.start_date, planning.end_date),
    [planning.start_date, planning.end_date]
  );

  const selectedDay: PosteDayVm | null = selected ? byDate.get(selected) ?? null : null;
  const selectedWeek = selectedDay ? isoWeekRangeFrom(selectedDay.day_date) : null;

  useEffect(() => {
    if (!selectedDay) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSelected(null);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [selectedDay]);

  return (
    <section className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-5 shadow-sm">
      <div className="grid grid-cols-7 gap-3">
        {DAYS.map((d) => {
          const weekend = d.short === "Sam" || d.short === "Dim";
          return (
            <div
              key={d.short}
              className={[
                "px-2 text-sm font-semibold tracking-tight",
                weekend ? "text-[color:var(--app-text)]" : "text-[color:var(--app-text)]/80",
              ].join(" ")}
            >
              <span className="hidden md:inline">{d.full}</span>
              <span className="md:hidden">{d.short}</span>
            </div>
          );
        })}

        {allDates.map((date) => {
          const day = byDate.get(date);
          const outside = !isInSameMonth(date, anchorMonth);

          const isSelected = selected === date;
          const isWeek = selectedWeek ? date >= selectedWeek.start && date <= selectedWeek.end : false;

          // planning.days couvre la range, donc "day" devrait exister.
          // Mais on reste safe si jamais.
          if (!day) return <div key={date} className="rounded-xl border border-[color:var(--app-border)] opacity-50" />;

          return (
            <PosteDayCell
              key={date}
              day={day}
              isOutsideMonth={outside}
              isSelected={isSelected}
              isInSelectedWeek={isWeek}
              onSelect={() => setSelected(date)}
            />
          );
        })}
      </div>

      <PosteDaySheet
        open={!!selectedDay}
        onOpenChange={(o) => setSelected(o ? selected : null)}
        day={selectedDay}
        poste={planning.poste}
      />
    </section>
  );
}
