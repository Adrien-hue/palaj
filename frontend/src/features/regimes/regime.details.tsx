"use client";

import type { RegimeDetail } from "@/types";

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 py-2">
      <div className="text-xs font-medium text-zinc-600">{label}</div>
      <div className="text-sm text-zinc-900 text-right">{value}</div>
    </div>
  );
}

function show(v?: number | null) {
  return v == null ? "—" : v;
}

export default function RegimeDetails({ regime }: { regime: RegimeDetail }) {
  return (
    <div className="space-y-4">
      <div className="rounded-2xl bg-zinc-50 p-4 ring-1 ring-zinc-200">
        <div className="text-base font-semibold text-zinc-900">{regime.nom}</div>
        <div className="mt-1 text-xs text-zinc-600">ID: {regime.id}</div>
      </div>

      <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
        <div className="text-sm font-semibold text-zinc-900">Description</div>
        <div className="mt-2 text-sm text-zinc-700">{regime.desc || "—"}</div>
      </div>

      <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
        <div className="text-sm font-semibold text-zinc-900">Règles</div>
        <div className="mt-2">
          <Row label="Min RP annuels" value={show(regime.min_rp_annuels)} />
          <Row label="Min RP dimanches" value={show(regime.min_rp_dimanches)} />
          <Row label="Min RPSD" value={show(regime.min_rpsd)} />
          <Row label="Min RP 2+" value={show(regime.min_rp_2plus)} />
          <Row label="Min RP semestre" value={show(regime.min_rp_semestre)} />
        </div>
      </div>

      <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
        <div className="text-sm font-semibold text-zinc-900">Moyennes</div>
        <div className="mt-2">
          <Row label="Avg service (min)" value={show(regime.avg_service_minutes)} />
          <Row label="Avg tolerance (min)" value={show(regime.avg_tolerance_minutes)} />
        </div>
      </div>

      <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
        <div className="flex items-center justify-between gap-4">
          <div className="text-sm font-semibold text-zinc-900">Agents</div>
          <div className="text-xs text-zinc-600">{regime.agents?.length ?? 0}</div>
        </div>

        {regime.agents?.length ? (
          <div className="mt-3 space-y-2">
            {regime.agents.slice(0, 10).map((a) => (
              <div
                key={a.id}
                className="flex items-center justify-between gap-4 rounded-xl bg-zinc-50 px-3 py-2 ring-1 ring-zinc-100"
              >
                <div className="text-sm text-zinc-900">
                  {a.nom} {a.prenom}
                </div>
                <div className="text-xs text-zinc-600">#{a.id}</div>
              </div>
            ))}
            {regime.agents.length > 10 ? (
              <div className="text-xs text-zinc-500">
                +{regime.agents.length - 10} autres…
              </div>
            ) : null}
          </div>
        ) : (
          <div className="mt-2 text-sm text-zinc-600">Aucun agent associé.</div>
        )}
      </div>
    </div>
  );
}
