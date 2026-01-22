"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { addMonthsISO, monthAnchorISO } from "@/features/planning/utils/month.utils";

const MONTHS_FR = [
  "Janvier","Février","Mars","Avril","Mai","Juin",
  "Juillet","Août","Septembre","Octobre","Novembre","Décembre",
];

export function PosteMonthControls() {
  const router = useRouter();
  const sp = useSearchParams();

  const date = sp.get("date") ?? new Date().toISOString().slice(0, 10);
  const anchor = monthAnchorISO(date);

  const year = Number(anchor.slice(0, 4));
  const monthIndex = Number(anchor.slice(5, 7)) - 1;

  function push(nextAnchor: string) {
    const next = new URLSearchParams(sp.toString());
    next.set("date", nextAnchor);
    router.push(`?${next.toString()}`);
  }

  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <Button variant="outline" size="icon" onClick={() => push(addMonthsISO(anchor, -1))} title="Mois précédent">
        <ChevronLeft className="h-4 w-4" />
      </Button>

      <select
        className="h-9 rounded-md border border-[color:var(--app-border)] bg-[color:var(--app-surface)] px-3 text-sm text-[color:var(--app-text)]"
        value={monthIndex}
        onChange={(e) => {
          const mi = Number(e.target.value);
          push(`${year}-${String(mi + 1).padStart(2, "0")}-01`);
        }}
        aria-label="Sélection du mois"
      >
        {MONTHS_FR.map((m, i) => (
          <option key={m} value={i}>{m}</option>
        ))}
      </select>

      <input
        type="number"
        className="h-9 w-24 rounded-md border border-[color:var(--app-border)] bg-[color:var(--app-surface)] px-3 text-sm text-[color:var(--app-text)]"
        value={year}
        onChange={(e) => {
          const y = Number(e.target.value);
          if (!Number.isFinite(y)) return;
          push(`${y}-${String(monthIndex + 1).padStart(2, "0")}-01`);
        }}
        aria-label="Année"
      />

      <Button variant="outline" size="icon" onClick={() => push(addMonthsISO(anchor, 1))} title="Mois suivant">
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  );
}
