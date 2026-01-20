"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { addMonthsISO, monthAnchorISO, monthLabelFR } from "../utils/month.utils";

const MONTHS_FR = [
  "Janvier","Février","Mars","Avril","Mai","Juin",
  "Juillet","Août","Septembre","Octobre","Novembre","Décembre",
];

export function MonthControls() {
  const router = useRouter();
  const sp = useSearchParams();

  const date = sp.get("date") ?? new Date().toISOString().slice(0, 10);
  const anchor = monthAnchorISO(date);

  const label = monthLabelFR(anchor);
  const year = Number(anchor.slice(0, 4));
  const monthIndex = Number(anchor.slice(5, 7)) - 1;

  function push(nextAnchor: string) {
    const next = new URLSearchParams(sp.toString());
    next.set("date", nextAnchor);
    router.replace(`?${next.toString()}`);
  }

  const controlClass =
    "rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] px-3 py-2 text-sm text-[color:var(--app-text)] transition " +
    "hover:bg-[color:var(--app-soft)] hover:ring-1 hover:ring-[color:var(--app-ring)] hover:ring-inset " +
    "focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900/10";

  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          className={controlClass}
          onClick={() => push(addMonthsISO(anchor, -1))}
          title="Mois précédent"
          aria-label="Mois précédent"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>

        <select
          className={controlClass}
          value={monthIndex}
          onChange={(e) => {
            const mi = Number(e.target.value);
            push(`${year}-${String(mi + 1).padStart(2, "0")}-01`);
          }}
          aria-label="Sélection du mois"
        >
          {MONTHS_FR.map((m, i) => (
            <option key={m} value={i}>
              {m}
            </option>
          ))}
        </select>

        <input
          type="number"
          min={1900}
          max={2100}
          step={1}
          className={controlClass + " w-24"}
          value={year}
          onChange={(e) => {
            const y = Number(e.target.value);
            if (!Number.isFinite(y)) return;
            push(`${y}-${String(monthIndex + 1).padStart(2, "0")}-01`);
          }}
          aria-label="Année"
        />

        <button
          type="button"
          className={controlClass}
          onClick={() => push(addMonthsISO(anchor, 1))}
          title="Mois suivant"
          aria-label="Mois suivant"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
