"use client";

import { useMemo } from "react";

import type {
  PostePlanningVm,
  PosteDayVm,
} from "@/features/planning-poste/vm/postePlanning.vm";

import { PlanningGridBase } from "@/components/planning/PlanningGridBase";
import { PosteDayCell } from "./PosteDayCell";

type Common = {
  planning: PostePlanningVm;

  selectedDate?: string | null;
  onSelectedDateChange?: (date: string | null) => void;

  multiSelect?: boolean;
  multiSelectedDates?: Set<string>;
  onMultiSelectDay?: (
    day: PosteDayVm,
    e: React.MouseEvent<HTMLButtonElement>
  ) => void;

  onDayClick?: (day: PosteDayVm) => void;

  height?: number | string;
  weekStartsOn?: 0 | 1;
  closeOnEscape?: boolean;
};


type PostePlanningGridProps =
  | (Common & {
      mode: "month";
      anchorMonth: string; // ISO YYYY-MM-DD (any day in month)
    })
  | (Common & {
      mode: "range";
      startDate: string; // ISO YYYY-MM-DD
      endDate: string; // ISO YYYY-MM-DD
      alignToWeeks?: boolean;
    });

export function PostePlanningGrid(props: PostePlanningGridProps) {
  const { planning } = props;

  const byDate = useMemo(
    () => new Map(planning.days.map((d) => [d.day_date, d] as const)),
    [planning.days]
  );

  const isMulti = !!props.multiSelect;

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
      closeOnEscape={props.closeOnEscape}
      gridLabel="Planning poste"
      renderCell={({ day, isOutsideMonth, isSelected, isInSelectedWeek, onSelect }) => {
        const dayDate = day?.day_date ?? null;

        const isMultiSelected =
          !!dayDate && (props.multiSelectedDates?.has(dayDate) ?? false);

        return (
          <PosteDayCell
            day={day}
            isOutsideMonth={isOutsideMonth}
            isSelected={isSelected}
            isInSelectedWeek={isInSelectedWeek}
            multiSelect={isMulti}
            isMultiSelected={isMultiSelected}
            onSelect={(e) => {
              if (isMulti) {
                if (day && props.onMultiSelectDay) {
                  props.onMultiSelectDay(day, e);
                }
                return;
              }

              onSelect();

              if (day && props.onDayClick) props.onDayClick(day);
            }}
          />
        );
      }}
      renderDetails={() => null}
    />
  );
}
