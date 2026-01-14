"use client";

import type { PosteDetail } from "@/types";

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 py-2">
      <div className="text-xs font-medium text-zinc-600">{label}</div>
      <div className="text-sm text-zinc-900 text-right">{value}</div>
    </div>
  );
}

function formatTime(t: string) {
  // "06:00:00" -> "06:00"
  return t?.slice(0, 5) ?? "—";
}

export default function PosteDetails({ poste }: { poste: PosteDetail }) {
  const tranches = poste.tranches ?? [];
  const qualifications = poste.qualifications ?? [];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="rounded-2xl bg-zinc-50 p-4 ring-1 ring-zinc-200">
        <div className="text-base font-semibold text-zinc-900">{poste.nom}</div>
        <div className="mt-1 text-xs text-zinc-600">ID: {poste.id}</div>
      </div>

      {/* Résumé */}
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
          <div className="text-sm font-semibold text-zinc-900">Tranches</div>
          <div className="mt-1 text-sm text-zinc-700">{tranches.length} au total</div>
          <div className="mt-1 text-xs text-zinc-500">Horaires associés à ce poste.</div>
        </div>

        <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
          <div className="text-sm font-semibold text-zinc-900">Qualifications</div>
          <div className="mt-1 text-sm text-zinc-700">{qualifications.length} au total</div>
          <div className="mt-1 text-xs text-zinc-500">Agents qualifiés sur ce poste.</div>
        </div>
      </div>

      {/* Tranches (liste courte, utile) */}
      <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
        <div className="flex items-center justify-between gap-4">
          <div className="text-sm font-semibold text-zinc-900">Tranches</div>
          <div className="text-xs text-zinc-600">{tranches.length}</div>
        </div>

        {tranches.length === 0 ? (
          <div className="mt-2 text-sm text-zinc-600">Aucune tranche.</div>
        ) : (
          <div className="mt-3 space-y-2">
            {tranches.map((t) => (
              <div
                key={t.id}
                className="flex items-center justify-between gap-4 rounded-xl bg-zinc-50 px-3 py-2 ring-1 ring-zinc-100"
              >
                <div className="text-sm text-zinc-900">{t.nom}</div>
                <div className="text-xs text-zinc-600">
                  {formatTime(t.heure_debut)} → {formatTime(t.heure_fin)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Qualifications (afficher juste un aperçu, car pas de nom d’agent ici) */}
      <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
        <div className="flex items-center justify-between gap-4">
          <div className="text-sm font-semibold text-zinc-900">Qualifications</div>
          <div className="text-xs text-zinc-600">{qualifications.length}</div>
        </div>

        {qualifications.length === 0 ? (
          <div className="mt-2 text-sm text-zinc-600">Aucune qualification.</div>
        ) : (
          <div className="mt-3 space-y-2">
            {qualifications.slice(0, 10).map((q) => (
              <div
                key={`${q.agent_id}-${q.poste_id}`}
                className="flex items-center justify-between gap-4 rounded-xl bg-zinc-50 px-3 py-2 ring-1 ring-zinc-100"
              >
                <div className="text-sm text-zinc-900">Agent #{q.agent_id}</div>
                <div className="text-xs text-zinc-600">{q.date_qualification ?? "—"}</div>
              </div>
            ))}
            {qualifications.length > 10 && (
              <div className="text-xs text-zinc-500">
                +{qualifications.length - 10} autres…
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
