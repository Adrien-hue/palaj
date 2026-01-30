"use client";

import { useMemo } from "react";

import type { AgentPlanningVm, AgentDayVm } from "../vm/agentPlanning.vm";
import { PlanningGridBase } from "@/components/planning/PlanningGridBase";

import { AgentDayCell } from "./AgentDayCell";
import { AgentDaySheet } from "./AgentDaySheet";

type AgentPlanningGridProps =
  | {
      mode: "month";
      anchorMonth: string; // ISO YYYY-MM-DD (any day in month)
      planning: AgentPlanningVm;
      posteNameById: Map<number, string>;
    }
  | {
      mode: "range";
      startDate: string; // ISO YYYY-MM-DD
      endDate: string; // ISO YYYY-MM-DD
      planning: AgentPlanningVm;
      posteNameById: Map<number, string>;
    };

export function AgentPlanningGrid(props: AgentPlanningGridProps) {
  const { planning, posteNameById } = props;

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
      renderCell={({ day, isOutsideMonth, isSelected, isInSelectedWeek, onSelect }) => (
        <AgentDayCell
          day={day}
          isOutsideMonth={isOutsideMonth}
          isSelected={isSelected}
          isInSelectedWeek={isInSelectedWeek}
          onSelect={onSelect}
          posteNameById={posteNameById}
        />
      )}
      renderDetails={({ open, selectedDay, close }) => (
        <AgentDaySheet
          open={open}
          onClose={close}
          selectedDay={selectedDay}
          posteNameById={posteNameById}
        />
      )}
      closeOnEscape
      gridLabel="Planning agent"
    />
  );
}
