import Link from "next/link";
import { ChevronLeft } from "lucide-react";

import type { Poste } from "@/types/postes";
import { monthLabelFR } from "@/features/planning/utils/month.utils";

import { Button } from "@/components/ui/button";
import { PosteMonthControls } from "./PosteMonthControls";

export function PostePlanningHeader({
  poste,
  anchorMonth,
}: {
  poste: Poste;
  anchorMonth: string;
}) {
  const label = monthLabelFR(anchorMonth);

  return (
    <section className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <nav className="flex items-center gap-2 text-sm text-[color:var(--app-muted)]">
          <Link
            href="/app"
            className="rounded-md px-1.5 py-0.5 transition hover:bg-[color:var(--app-soft)] hover:text-[color:var(--app-text)]"
          >
            Planning
          </Link>
          <span className="opacity-60">/</span>
          <Link
            href="/app/planning/postes"
            className="rounded-md px-1.5 py-0.5 transition hover:bg-[color:var(--app-soft)] hover:text-[color:var(--app-text)]"
          >
            Par poste
          </Link>
          <span className="opacity-60">/</span>
          <span className="font-medium text-[color:var(--app-text)]">{poste.nom}</span>
        </nav>

        <div className="text-sm text-[color:var(--app-muted)]">
          <span className="font-semibold text-[color:var(--app-text)]">{label}</span>
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-3">
          <Button asChild variant="outline" className="w-fit">
            <Link href="/app/planning/postes">
              <ChevronLeft className="mr-2 h-4 w-4" />
              Retour
            </Link>
          </Button>

          <div>
            <div className="text-2xl font-semibold text-[color:var(--app-text)]">
              {poste.nom}
            </div>
            <div className="text-sm text-[color:var(--app-muted)]">
              Couverture mensuelle
            </div>
          </div>
        </div>

        <PosteMonthControls />
      </div>
    </section>
  );
}
