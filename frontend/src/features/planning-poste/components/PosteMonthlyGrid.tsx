"use client";

import { useEffect, useMemo, useState } from "react";
import type { PostePlanningDto } from "../mock/postePlanning.mock";
import { buildMonthDays, isoWeekRangeFrom, isSameMonth } from "../utils/month";
import { PosteDayCell } from "./PosteDayCell";
import { PosteDayDrawer } from "./PosteDayDrawer";

const DAYS = [
  { short: "Lun", full: "Lundi" },
  { short: "Mar", full: "Mardi" },
  { short: "Mer", full: "Mercredi" },
  { short: "Jeu", full: "Jeudi" },
  { short: "Ven", full: "Vendredi" },
  { short: "Sam", full: "Samedi" },
  { short: "Dim", full: "Dimanche" },
] as const;

export function PosteMonthlyGrid({
  anchorMonth,
  data,
}: {
  anchorMonth: string; // YYYY-MM-01
  data: PostePlanningDto;
}) {
  const [selected, setSelected] = useState<string | null>(null);

  const allDates = useMemo(() => buildMonthDays(anchorMonth), [anchorMonth]);

  const byDate = useMemo(() => {
    const m = new Map<string, PostePlanningDto["days"][number]>();
    data.days.forEach((d) => m.set(d.day_date, d));
    return m;
  }, [data.days]);

  const selectedDay = selected ? byDate.get(selected) ?? null : null;
  const selectedWeek = selectedDay ? isoWeekRangeFrom(selectedDay.day_date) : null;

  // total tranches = déduit des tranches rencontrées (POC)
  const totalTranches = useMemo(() => {
    const set = new Set<number>();
    data.days.forEach((d) => d.assignment.forEach((a) => set.add(a.tranche.id)));
    return Math.max(1, set.size);
  }, [data.days]);

  // UX: Esc close drawer
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
        {DAYS.map((d) => {
          const isWeekend = d.short === "Sam" || d.short === "Dim";
          return (
            <div
              key={d.short}
              className={[
                "px-2 text-sm font-semibold tracking-tight",
                isWeekend ? "text-[color:var(--app-text)]" : "text-[color:var(--app-text)]/80",
              ].join(" ")}
            >
              <span className="hidden md:inline">{d.full}</span>
              <span className="md:hidden">{d.short}</span>
            </div>
          );
        })}

        {allDates.map((date) => {
          const day = byDate.get(date) ?? { day_date: date, assignment: [] };
          const outside = !isSameMonth(date, anchorMonth);
          const isSelected = selected === date;
          const isWeek = selectedWeek ? date >= selectedWeek.start && date <= selectedWeek.end : false;

          return (
            <PosteDayCell
              key={date}
              day={day}
              isOutsideMonth={outside}
              isSelected={isSelected}
              isInSelectedWeek={isWeek}
              onSelect={() => setSelected(date)}
              totalTranches={totalTranches}
            />
          );
        })}
      </div>

      <PosteDayDrawer open={!!selectedDay} onClose={() => setSelected(null)} day={selectedDay} />
    </section>
  );
}
