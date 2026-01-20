"use client";

import { useSearchParams } from "next/navigation";
import { monthAnchorISO, monthLabelFR } from "../utils/month.utils";

export function MonthLabel() {
  const sp = useSearchParams();
  const date = sp.get("date") ?? new Date().toISOString().slice(0, 10);
  const anchor = monthAnchorISO(date);
  const label = monthLabelFR(anchor);

  return (
    <div className="text-sm font-semibold text-[color:var(--app-text)]" aria-live="polite">
      {label}
    </div>
  );
}
