"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { addMonthsISO, monthAnchorISO, monthLabelFR } from "@/features/planning-common/utils/month.utils";

export function usePlanningMonthParam() {
  const router = useRouter();
  const sp = useSearchParams();

  const date = sp.get("date") ?? new Date().toISOString().slice(0, 10);
  const anchor = monthAnchorISO(date);

  const label = monthLabelFR(anchor);
  const year = Number(anchor.slice(0, 4));
  const monthIndex = Number(anchor.slice(5, 7)) - 1;

  function setAnchor(nextAnchor: string, mode: "push" | "replace" = "push") {
    const next = new URLSearchParams(sp.toString());
    next.set("date", nextAnchor);
    const url = `?${next.toString()}`;
    if (mode === "replace") router.replace(url);
    else router.push(url);
  }

  function stepMonth(delta: number, mode: "push" | "replace" = "push") {
    setAnchor(addMonthsISO(anchor, delta), mode);
  }

  return { date, anchor, label, year, monthIndex, setAnchor, stepMonth };
}
