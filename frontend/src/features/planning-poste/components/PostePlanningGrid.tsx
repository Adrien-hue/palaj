"use client";

import { useMemo } from "react";

import type {
  PostePlanningVm,
  PosteDayVm,
} from "@/features/planning-poste/vm/postePlanning.vm";

import { PlanningGridBase } from "@/components/planning/PlanningGridBase";
import { PosteDayCell } from "./PosteDayCell";

type PostePlanningGridProps =
  | {
      mode: "month";
      anchorMonth: string; // ISO YYYY-MM-DD (any day in month)
      planning: PostePlanningVm;

      selectedDate: string | null;
      onSelectedDateChange: (date: string | null) => void;

      height?: number | string;
      weekStartsOn?: 0 | 1;

      closeOnEscape?: boolean;
    }
  | {
      mode: "range";
      startDate: string; // ISO YYYY-MM-DD
      endDate: string; // ISO YYYY-MM-DD
      planning: PostePlanningVm;

      selectedDate: string | null;
      onSelectedDateChange: (date: string | null) => void;

      height?: number | string;
      weekStartsOn?: 0 | 1;
      alignToWeeks?: boolean;

      closeOnEscape?: boolean;
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
      selectedDate={props.selectedDate}
      onSelectedDateChange={props.onSelectedDateChange}
      renderCell={({ day, isOutsideMonth, isSelected, isInSelectedWeek, onSelect }) => (
        <PosteDayCell
          day={day}
          isOutsideMonth={isOutsideMonth}
          isSelected={isSelected}
          isInSelectedWeek={isInSelectedWeek}
          onSelect={() => {
            onSelect();

            props.onSelectedDateChange(day ? day.day_date : null);
          }}
        />
      )}
      renderDetails={() => null}
      closeOnEscape={props.closeOnEscape}
      gridLabel="Planning poste"
    />
  );
}
