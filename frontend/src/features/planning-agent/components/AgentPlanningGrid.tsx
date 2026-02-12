"use client";

import type { MouseEvent as ReactMouseEvent } from "react";
import { useMemo } from "react";

import type { AgentPlanningVm, AgentDayVm } from "../vm/agentPlanning.vm";
import { PlanningGridBase } from "@/components/planning/PlanningGridBase";

import type { RhViolation } from "@/types/rhValidation";
import type { RhDayIndex } from "@/features/rh-validation/utils/buildRhDayIndex";

import { AgentDayCell } from "./AgentDayCell";

type AgentPlanningGridProps =
  | {
      mode: "month";
      anchorMonth: string; // ISO YYYY-MM-DD
      planning: AgentPlanningVm;
      onDayClick?: (day: AgentDayVm) => void;

      multiSelect?: boolean;
      multiSelectedDates?: ReadonlySet<string>;
      onMultiSelectDay?: (
        day: AgentDayVm,
        e: ReactMouseEvent<HTMLButtonElement>,
      ) => void;
      rhDayIndex?: RhDayIndex;
    }
  | {
      mode: "range";
      startDate: string; // ISO YYYY-MM-DD
      endDate: string; // ISO YYYY-MM-DD
      planning: AgentPlanningVm;
      onDayClick?: (day: AgentDayVm) => void;

      multiSelect?: boolean;
      multiSelectedDates?: ReadonlySet<string>;
      onMultiSelectDay?: (
        day: AgentDayVm,
        e: ReactMouseEvent<HTMLButtonElement>,
      ) => void;
      rhDayIndex?: RhDayIndex;
    };

export function AgentPlanningGrid(props: AgentPlanningGridProps) {
  const { planning } = props;

  const byDate = useMemo(
    () =>
      new Map(planning.days.map((d) => [d.day_date.slice(0, 10), d] as const)),
    [planning.days],
  );

  return (
    <PlanningGridBase<AgentDayVm>
      {...(props.mode === "month"
        ? { mode: "month" as const, anchorMonth: props.anchorMonth }
        : {
            mode: "range" as const,
            startDate: props.startDate,
            endDate: props.endDate,
          })}
      getDay={(iso) => byDate.get(iso)}
      getDayDate={(day) => day.day_date}
      renderCell={({
        day,
        isOutsideMonth,
        isSelected,
        isInSelectedWeek,
        isOutsideRange,
        onSelect,
      }) => {
        const dayKey = day.day_date.slice(0, 10);

        return (
          <AgentDayCell
            day={day}
            isOutsideMonth={isOutsideMonth}
            isOutsideRange={isOutsideRange}
            isSelected={isSelected}
            isInSelectedWeek={isInSelectedWeek}
            isMultiSelected={props.multiSelectedDates?.has(dayKey) ?? false}
            rhViolations={props.rhDayIndex?.[dayKey] ?? []}
            onSelect={(e) => {
              if (props.multiSelect) {
                props.onMultiSelectDay?.(day, e);
                return;
              }

              onSelect();
              props.onDayClick?.(day);
            }}
          />
        );
      }}
      renderDetails={() => null}
      closeOnEscape
      gridLabel="Planning agent"
    />
  );
}
