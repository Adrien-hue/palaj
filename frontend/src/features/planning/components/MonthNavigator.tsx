"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { addMonthsISO, monthAnchorISO, monthLabelFR } from "../utils/month.utils";

const MONTHS_FR = [
  "Janvier","Février","Mars","Avril","Mai","Juin",
  "Juillet","Août","Septembre","Octobre","Novembre","Décembre",
];

export function MonthNavigator() {
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
    router.push(`?${next.toString()}`);
  }

  return (
    <div className="mb-5 rounded-2xl border border-border bg-card p-4 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-sm text-muted-foreground">Mois</div>
          <div className="text-base font-semibold text-foreground">{label}</div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            className="rounded-xl border border-border bg-background px-3 py-2 text-sm text-foreground shadow-sm hover:bg-muted"
            onClick={() => push(addMonthsISO(anchor, -1))}
            title="Mois précédent"
          >
            ←
          </button>

          <select
            className="rounded-xl border border-border bg-background px-3 py-2 text-sm text-foreground"
            value={monthIndex}
            onChange={(e) => {
              const mi = Number(e.target.value);
              push(`${year}-${String(mi + 1).padStart(2, "0")}-01`);
            }}
          >
            {MONTHS_FR.map((m, i) => (
              <option key={m} value={i}>{m}</option>
            ))}
          </select>

          <input
            type="number"
            className="w-24 rounded-xl border border-border bg-background px-3 py-2 text-sm text-foreground"
            value={year}
            onChange={(e) => {
              const y = Number(e.target.value);
              if (!Number.isFinite(y)) return;
              push(`${y}-${String(monthIndex + 1).padStart(2, "0")}-01`);
            }}
          />

          <button
            className="rounded-xl border border-border bg-background px-3 py-2 text-sm text-foreground shadow-sm hover:bg-muted"
            onClick={() => push(addMonthsISO(anchor, 1))}
            title="Mois suivant"
          >
            →
          </button>
        </div>
      </div>
    </div>
  );
}
