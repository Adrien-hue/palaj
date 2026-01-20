// src/app/app/page.tsx
import Link from "next/link";

export default function AppHomePage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-zinc-950">Planning</h1>
      <p className="text-zinc-600">
        Choisis une vue pour consulter et modifier les plannings.
      </p>

      <div className="grid gap-3 md:grid-cols-3">
        <Link
          href="/app/planning/agents"
          className="rounded-lg border border-zinc-200 bg-white p-4 hover:bg-zinc-50"
        >
          <div className="font-medium">Par agent</div>
          <div className="mt-1 text-sm text-zinc-600">
            Visualiser et modifier agent par agent
          </div>
        </Link>

        <Link
          href="/app/planning/postes"
          className="rounded-lg border border-zinc-200 bg-white p-4 hover:bg-zinc-50"
        >
          <div className="font-medium">Par poste</div>
          <div className="mt-1 text-sm text-zinc-600">
            Vue planning par poste (à construire)
          </div>
        </Link>

        <Link
          href="/app/planning/groupes"
          className="rounded-lg border border-zinc-200 bg-white p-4 hover:bg-zinc-50"
        >
          <div className="font-medium">Par groupe</div>
          <div className="mt-1 text-sm text-zinc-600">
            Vue planning par groupe de postes (à construire)
          </div>
        </Link>
      </div>
    </div>
  );
}
