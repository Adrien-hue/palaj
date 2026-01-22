"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";

import { buildDaysRange, isInSameMonth } from "@/features/planning-common/utils/month.utils";
import { isoWeekRangeFrom } from "@/features/planning-common/utils/planning.utils";

const DAYS = [
  { short: "Lun", full: "Lundi" },
  { short: "Mar", full: "Mardi" },
  { short: "Mer", full: "Mercredi" },
  { short: "Jeu", full: "Jeudi" },
  { short: "Ven", full: "Vendredi" },
  { short: "Sam", full: "Samedi" },
  { short: "Dim", full: "Dimanche" },
] as const;

export type MonthlyGridCellRenderArgs<TDay> = {
  date: string; // ISO YYYY-MM-DD
  day: TDay;
  isOutsideMonth: boolean;
  isSelected: boolean;
  isInSelectedWeek: boolean;
  onSelect: () => void;
};

export function MonthlyGridBase<TDay>({
  anchorMonth,
  startDate,
  endDate,

  getDay,
  getDayDate,

  renderCell,
  renderDetails,

  closeOnEscape = true,
  gridLabel = "Planning mensuel",
}: {
  anchorMonth: string; // ISO YYYY-MM-DD (any day inside month)
  startDate: string; // ISO YYYY-MM-DD
  endDate: string; // ISO YYYY-MM-DD

  getDay: (isoDate: string) => TDay | undefined;
  getDayDate: (day: TDay) => string; // ISO YYYY-MM-DD

  renderCell: (args: MonthlyGridCellRenderArgs<TDay>) => React.ReactNode;
  renderDetails: (args: {
    open: boolean;
    selectedDate: string | null;
    selectedDay: TDay | null;
    close: () => void;
    setSelectedDate: (d: string | null) => void;
  }) => React.ReactNode;

  closeOnEscape?: boolean;
  gridLabel?: string;
}) {
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const allDates = useMemo(() => buildDaysRange(startDate, endDate), [startDate, endDate]);

  const selectedDay = selectedDate ? getDay(selectedDate) ?? null : null;

  const selectedWeek = useMemo(() => {
    if (!selectedDay) return null;
    return isoWeekRangeFrom(getDayDate(selectedDay));
  }, [selectedDay, getDayDate]);

  useEffect(() => {
    if (!closeOnEscape) return;
    if (!selectedDay) return;

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSelectedDate(null);
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [selectedDay, closeOnEscape]);

  return (
    <Card className="border-[color:var(--app-border)] bg-[color:var(--app-surface)] shadow-sm">
      <CardContent className="p-5">
        <div className="grid grid-cols-7 gap-2 md:gap-3" role="grid" aria-label={gridLabel}>
          {DAYS.map((d) => {
            const weekend = d.short === "Sam" || d.short === "Dim";
            return (
              <div
                key={d.short}
                role="columnheader"
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
            const day = getDay(date);
            const outside = !isInSameMonth(date, anchorMonth);

            const isSelected = selectedDate === date;
            const isWeek = selectedWeek ? date >= selectedWeek.start && date <= selectedWeek.end : false;

            if (!day) {
              return (
                <div
                  key={date}
                  role="gridcell"
                  aria-disabled="true"
                  className="rounded-xl border border-[color:var(--app-border)] opacity-50"
                />
              );
            }

            return (
              <div key={date} role="gridcell">
                {renderCell({
                  date,
                  day,
                  isOutsideMonth: outside,
                  isSelected,
                  isInSelectedWeek: isWeek,
                  onSelect: () => setSelectedDate(date),
                })}
              </div>
            );
          })}
        </div>

        {renderDetails({
          open: !!selectedDay,
          selectedDate,
          selectedDay,
          close: () => setSelectedDate(null),
          setSelectedDate,
        })}
      </CardContent>
    </Card>
  );
}
