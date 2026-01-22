"use client";

import { useMemo } from "react";

import type { PostePlanningVm, PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";
import { MonthlyGridBase } from "@/features/planning-common";

import { PosteDayCell } from "./PosteDayCell";
import { PosteDaySheet } from "./PosteDaySheet";

export function PosteMonthlyPlanningGrid({
  anchorMonth,
  planning,
}: {
  anchorMonth: string;
  planning: PostePlanningVm;
}) {
  const byDate = useMemo(
    () => new Map(planning.days.map((d) => [d.day_date, d] as const)),
    [planning.days]
  );

  return (
    <MonthlyGridBase<PosteDayVm>
      anchorMonth={anchorMonth}
      startDate={planning.start_date}
      endDate={planning.end_date}
      getDay={(iso) => byDate.get(iso)}
      getDayDate={(day) => day.day_date}
      renderCell={({ day, isOutsideMonth, isSelected, isInSelectedWeek, onSelect }) => (
        <PosteDayCell
          day={day}
          isOutsideMonth={isOutsideMonth}
          isSelected={isSelected}
          isInSelectedWeek={isInSelectedWeek}
          onSelect={onSelect}
        />
      )}
      renderDetails={({ open, selectedDay, close }) => (
        <PosteDaySheet
          open={open}
          onOpenChange={(o) => {
            if (!o) close();
          }}
          day={selectedDay}
          poste={planning.poste}
        />
      )}
      closeOnEscape={true}
      gridLabel="Planning poste"
    />
  );
}
