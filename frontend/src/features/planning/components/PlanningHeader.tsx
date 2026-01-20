import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { MonthControls } from "./MonthControls";
import { MonthLabel } from "./MonthLabel";

export function PlanningHeader({
  agentName,
  backHref = "/app/planning/agents",
}: {
  agentName: string;
  backHref?: string;
}) {
  return (
    <section className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-5 shadow-sm">
      {/* Row 1: breadcrumb (left) / month label (right) */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <nav className="flex items-center gap-2 text-sm text-[color:var(--app-muted)]">
          <Link
            href="/app"
            className="rounded-md px-1.5 py-0.5 transition hover:bg-[color:var(--app-soft)] hover:text-[color:var(--app-text)]"
          >
            Planning
          </Link>

          <ChevronRight className="h-4 w-4 opacity-60" />

          <Link
            href={backHref}
            className="rounded-md px-1.5 py-0.5 transition hover:bg-[color:var(--app-soft)] hover:text-[color:var(--app-text)]"
          >
            Par agent
          </Link>

          <ChevronRight className="h-4 w-4 opacity-60" />

          <span className="font-medium text-[color:var(--app-text)]">
            {agentName}
          </span>
        </nav>

        <div className="flex items-center gap-2 text-sm text-[color:var(--app-muted)]">
          <span>Mois</span>
          <span className="font-semibold text-[color:var(--app-text)]">
            <MonthLabel />
          </span>
        </div>
      </div>

      {/* Row 2: left block (back + title) / right block (controls) */}
      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-3">
          <Link
            href={backHref}
            className="inline-flex w-fit items-center gap-2 rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-bg)] px-3 py-2 text-sm font-medium text-[color:var(--app-text)] transition hover:bg-[color:var(--app-soft)] hover:ring-1 hover:ring-[color:var(--app-ring)] hover:ring-inset focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900/10"
            title="Retour à la liste des agents"
          >
            <ChevronLeft className="h-4 w-4" />
            Retour
          </Link>

          <div>
            <div className="text-2xl font-semibold text-[color:var(--app-text)]">
              {agentName}
            </div>
            <div className="text-sm text-[color:var(--app-muted)]">
              Planning mensuel
            </div>
          </div>
        </div>

        <div className="sm:pb-0.5">
          <MonthControls />
        </div>
      </div>
    </section>
  );
}
