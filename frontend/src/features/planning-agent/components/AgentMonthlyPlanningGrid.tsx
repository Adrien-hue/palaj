"use client";

import { useMemo } from "react";

import type { AgentPlanningVm, AgentDayVm } from "../vm/agentPlanning.vm";
import { MonthlyGridBase } from "@/features/planning-common";

import { AgentDayCell } from "./AgentDayCell";
import { AgentDaySheet } from "./AgentDaySheet";

export function AgentMonthlyPlanningGrid({
  anchorMonth,
  planning,
  posteNameById,
}: {
  anchorMonth: string;
  planning: AgentPlanningVm;
  posteNameById: Map<number, string>;
}) {
  const byDate = useMemo(
    () => new Map(planning.days.map((d) => [d.day_date, d] as const)),
    [planning.days]
  );

  return (
    <MonthlyGridBase<AgentDayVm>
      anchorMonth={anchorMonth}
      startDate={planning.start_date}
      endDate={planning.end_date}
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
      closeOnEscape={true}
      gridLabel="Planning agent"
    />
  );
}
