"use client";

import { useMemo } from "react";

import type { AgentPlanningVm, AgentDayVm } from "../vm/agentPlanning.vm";
import { PlanningGridBase } from "@/components/planning/PlanningGridBase";

import { AgentDayCell } from "./AgentDayCell";

type AgentPlanningGridProps =
  | {
      mode: "month";
      anchorMonth: string; // ISO YYYY-MM-DD
      planning: AgentPlanningVm;
      onDayClick?: (day: AgentDayVm) => void;
    }
  | {
      mode: "range";
      startDate: string; // ISO YYYY-MM-DD
      endDate: string; // ISO YYYY-MM-DD
      planning: AgentPlanningVm;
      onDayClick?: (day: AgentDayVm) => void;
    };

export function AgentPlanningGrid(props: AgentPlanningGridProps) {
  const { planning } = props;

  const byDate = useMemo(
    () => new Map(planning.days.map((d) => [d.day_date, d] as const)),
    [planning.days]
  );

  return (
    <PlanningGridBase<AgentDayVm>
      {...(props.mode === "month"
        ? { mode: "month" as const, anchorMonth: props.anchorMonth }
        : { mode: "range" as const, startDate: props.startDate, endDate: props.endDate })}
      getDay={(iso) => byDate.get(iso)}
      getDayDate={(day) => day.day_date}
      renderCell={({ day, isOutsideMonth, isSelected, isInSelectedWeek, isOutsideRange, onSelect }) => (
        <AgentDayCell
          day={day}
          isOutsideMonth={isOutsideMonth}
          isOutsideRange={isOutsideRange}
          isSelected={isSelected}
          isInSelectedWeek={isInSelectedWeek}
          onSelect={() => {
            onSelect();
            props.onDayClick?.(day);
          }}
        />
      )}
      renderDetails={() => null}
      closeOnEscape
      gridLabel="Planning agent"
    />
  );
}
