"use client";

import { useMemo } from "react";

import type { PostePlanningVm, PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";
import { PlanningGridBase } from "@/components/planning/PlanningGridBase";

import { PosteDayCell } from "./PosteDayCell";
import { PosteDaySheet } from "./PosteDaySheet";

type PostePlanningGridProps =
  | {
      mode: "month";
      anchorMonth: string; // ISO YYYY-MM-DD (any day in month)
      planning: PostePlanningVm;

      // optional passthroughs to base
      height?: number | string;
      weekStartsOn?: 0 | 1;
    }
  | {
      mode: "range";
      startDate: string; // ISO YYYY-MM-DD
      endDate: string; // ISO YYYY-MM-DD
      planning: PostePlanningVm;

      // optional passthroughs to base
      height?: number | string;
      weekStartsOn?: 0 | 1;
      alignToWeeks?: boolean;
    };

export function PostePlanningGrid(props: PostePlanningGridProps) {
  const { planning } = props;

  const byDate = useMemo(
    () => new Map(planning.days.map((d) => [d.day_date, d] as const)),
    [planning.days]
  );

  return (
    <PlanningGridBase<PosteDayVm>
      {...(props.mode === "month"
        ? { mode: "month" as const, anchorMonth: props.anchorMonth }
        : {
            mode: "range" as const,
            startDate: props.startDate,
            endDate: props.endDate,
            alignToWeeks: props.alignToWeeks,
          })}
      weekStartsOn={props.weekStartsOn}
      maxHeight={props.height}
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
      closeOnEscape
      gridLabel="Planning poste"
    />
  );
}
