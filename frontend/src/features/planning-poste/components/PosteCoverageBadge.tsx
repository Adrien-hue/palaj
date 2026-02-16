import * as React from "react";
import { Badge } from "@/components/ui/badge";
import type { PosteDayVm } from "@/features/planning-poste/vm/postePlanning.vm";
import {
  computeTrancheCoverageCounts,
  trancheCoverageLabel,
  trancheCoverageRatio,
  trancheCoverageVariant,
} from "@/features/planning-poste/utils/posteCoverageTranches";

export function PosteCoverageBadge({ day }: { day: PosteDayVm }) {
  const c = computeTrancheCoverageCounts(day);

  return (
    <Badge
      variant={trancheCoverageVariant(c)}
      className="shrink-0 tabular-nums"
      title={trancheCoverageLabel(c)}
    >
      {trancheCoverageRatio(c)}
    </Badge>
  );
}
