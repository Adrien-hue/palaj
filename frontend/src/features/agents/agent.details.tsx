"use client";

import { useEffect, useMemo, useState } from "react";
import type { AgentDetails, Poste } from "@/types";
import { getPoste } from "@/services/postes.service";

function StatBadge({ active }: { active: boolean }) {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700",
      ].join(" ")}
    >
      {active ? "Actif" : "Inactif"}
    </span>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 py-2">
      <div className="text-xs font-medium text-zinc-600">{label}</div>
      <div className="text-sm text-zinc-900 text-right">{value}</div>
    </div>
  );
}

function formatMinutes(min?: number | null) {
  if (min == null) return "—";
  const h = Math.floor(min / 60);
  const m = min % 60;
  return `${h}h${String(m).padStart(2, "0")}`;
}

export default function AgentDetails({ agent }: { agent: AgentDetails }) {
  const qualifications = agent.qualifications ?? [];

  const posteIds = useMemo(() => {
    const set = new Set<number>();
    for (const q of qualifications) set.add(q.poste_id);
    return Array.from(set);
  }, [qualifications]);

  const [posteNames, setPosteNames] = useState<Record<number, string>>({});
  const [postesLoading, setPostesLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      if (posteIds.length === 0) {
        setPosteNames({});
        return;
      }

      setPostesLoading(true);
      try {
        const results = await Promise.allSettled(posteIds.map((id) => getPoste(id)));
        const map: Record<number, string> = {};

        results.forEach((r, idx) => {
          const id = posteIds[idx]!;
          if (r.status === "fulfilled") {
            const p = r.value as Poste;
            map[id] = p.nom;
          } else {
            map[id] = `Poste #${id}`;
          }
        });

        if (!cancelled) setPosteNames(map);
      } finally {
        if (!cancelled) setPostesLoading(false);
      }
    }

    run();
    return () => {
      cancelled = true;
    };
  }, [posteIds]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="rounded-2xl bg-zinc-50 p-4 ring-1 ring-zinc-200">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-base font-semibold text-zinc-900">
              {agent.nom} {agent.prenom}
            </div>
            <div className="mt-1 text-xs text-zinc-600">ID: {agent.id}</div>
          </div>
          <StatBadge active={agent.actif} />
        </div>

        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          <Row label="Code personnel" value={agent.code_personnel || "—"} />
          <Row label="Régime" value={agent.regime ? agent.regime.nom : agent.regime_id ?? "—"} />
        </div>
      </div>

      {/* Régime */}
      <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
        <div className="text-sm font-semibold text-zinc-900">Régime</div>

        {agent.regime ? (
          <div className="mt-2">
            <Row label="Nom" value={agent.regime.nom} />
            <Row label="Description" value={agent.regime.desc || "—"} />
          </div>
        ) : (
          <div className="mt-2 text-sm text-zinc-600">Aucun régime.</div>
        )}
      </div>

      {/* Qualifications */}
      <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
        <div className="flex items-center justify-between gap-4">
          <div className="text-sm font-semibold text-zinc-900">Qualifications</div>
          <div className="text-xs text-zinc-600">{qualifications.length} au total</div>
        </div>

        {qualifications.length === 0 ? (
          <div className="mt-2 text-sm text-zinc-600">Aucune qualification.</div>
        ) : (
          <div className="mt-3 space-y-2">
            {qualifications.map((q) => (
              <div
                key={`${agent.id}-${q.poste_id}`}
                className="flex items-center justify-between gap-4 rounded-xl bg-zinc-50 px-3 py-2 ring-1 ring-zinc-100"
              >
                <div className="text-sm text-zinc-900">
                  {posteNames[q.poste_id] ??
                    (postesLoading ? "Chargement..." : `Poste #${q.poste_id}`)}
                </div>
                <div className="text-xs text-zinc-600">
                  {q.date_qualification ? q.date_qualification : "—"}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}