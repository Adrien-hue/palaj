// frontend/src/features/planning-common/period/PlanningPeriodControls.tsx
"use client";

import { PlanningPeriodNavigator } from "@/components/planning/PlanningPeriodNavigator";
import { usePlanningPeriodParam } from "./usePlanningPeriodParam";

export function PlanningPeriodControls({
  navMode = "push",
}: {
  navMode?: "push" | "replace";
}) {
  const { period, setPeriod, step } = usePlanningPeriodParam({ navMode });

  return (
    <PlanningPeriodNavigator
      value={period}
      onChange={(p) => setPeriod(p, navMode)}
      onPrev={() => step(-1, navMode)}
      onNext={() => step(1, navMode)}
    />
  );
}
