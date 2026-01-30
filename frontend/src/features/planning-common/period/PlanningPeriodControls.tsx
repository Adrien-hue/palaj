"use client";

import type { PlanningPeriod } from "./period.types";
import { PlanningPeriodNavigator } from "@/components/planning/PlanningPeriodNavigator";

type Props = {
  value: PlanningPeriod;
  onChange: (p: PlanningPeriod) => void;
  onPrev: () => void;
  onNext: () => void;

  disabled?: boolean;
  className?: string;
};

export function PlanningPeriodControls({
  value,
  onChange,
  onPrev,
  onNext,
  disabled,
  className,
}: Props) {
  return (
    <PlanningPeriodNavigator
      value={value}
      onChange={onChange}
      onPrev={onPrev}
      onNext={onNext}
      disabled={disabled}
      className={className}
    />
  );
}
