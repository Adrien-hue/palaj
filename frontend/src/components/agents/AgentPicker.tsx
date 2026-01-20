"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Search, Clock, User, X } from "lucide-react";
import type { Agent } from "@/types";
import { ActiveSwitch } from "@/components/ui";

const RECENTS_KEY = "palaj.recents.agents";

function agentLabel(a: Agent) {
  return `${a.prenom} ${a.nom}`;
}

function initials(a: Agent) {
  const p = (a.prenom ?? "").trim();
  const n = (a.nom ?? "").trim();
  return `${p ? p[0] : ""}${n ? n[0] : ""}`.toUpperCase() || "•";
}

function formatMeta(a: Agent) {
  const parts: string[] = [];
  if (a.code_personnel) parts.push(a.code_personnel);
  return parts.join(" • ");
}

function normalize(s: string) {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "");
}

function loadRecents(): Agent[] {
  try {
    const raw = localStorage.getItem(RECENTS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Agent[];
    if (!Array.isArray(parsed)) return [];
    return parsed.slice(0, 8);
  } catch {
    return [];
  }
}

function saveRecent(agent: Agent) {
  try {
    const current = loadRecents();
    const next = [agent, ...current.filter((a) => a.id !== agent.id)].slice(
      0,
      8
    );
    localStorage.setItem(RECENTS_KEY, JSON.stringify(next));
  } catch {
    // ignore
  }
}

function SectionCard({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-5">
      <div className="mb-3 flex items-center gap-2 text-sm font-medium text-[color:var(--app-text)]">
        <span className="text-[color:var(--app-muted)]">{icon}</span>
        {title}
      </div>
      {children}
    </section>
  );
}

export function AgentPicker({
  agents,
  isLoading,
}: {
  agents: Agent[];
  isLoading?: boolean;
}) {
  const [includeInactive, setIncludeInactive] = useState(false);
  const [query, setQuery] = useState("");
  const [recents, setRecents] = useState<Agent[]>([]);

  useEffect(() => {
    setRecents(loadRecents());
  }, []);

  const filtered = useMemo(() => {
    const q = normalize(query.trim());

    const pool = includeInactive
      ? agents
      : agents.filter((a) => a.actif !== false);

    const base = q
      ? pool.filter((a) => {
          const hay = normalize(
            `${a.prenom} ${a.nom} ${a.code_personnel ?? ""} ${a.id}`
          );
          return hay.includes(q);
        })
      : pool;

    return [...base].sort((a, b) => {
      const an = normalize(a.nom ?? "");
      const bn = normalize(b.nom ?? "");
      if (an !== bn) return an.localeCompare(bn, "fr");

      const ap = normalize(a.prenom ?? "");
      const bp = normalize(b.prenom ?? "");
      return ap.localeCompare(bp, "fr");
    });
  }, [agents, query, includeInactive]);

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-4">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-[color:var(--app-soft)] text-[color:var(--app-soft-text)]">
            <Search className="h-4 w-4" />
          </div>

          <div className="flex-1">
            <div className="text-sm font-medium text-[color:var(--app-text)]">
              Rechercher un agent
            </div>
            <div className="relative mt-2">
              <input
                value={query}
                autoFocus
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Nom, prénom, matricule…"
                className="w-full rounded-lg border border-[color:var(--app-input-border)] bg-[color:var(--app-input-bg)] px-3 py-2 text-sm text-[color:var(--app-text)] placeholder:text-[color:var(--app-muted)] outline-none focus:ring-2 focus:ring-zinc-900/10"
              />

              {query && (
                <button
                  type="button"
                  onClick={() => setQuery("")}
                  title="Effacer la recherche"
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 text-[color:var(--app-muted)] transition hover:bg-[color:var(--app-soft)] hover:text-[color:var(--app-text)] focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900/10"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Recents */}
      {recents.length > 0 && (
        <SectionCard
          title="Récemment consultés"
          icon={<Clock className="h-4 w-4" />}
        >
          <div className="flex flex-wrap gap-2">
            {recents.map((a) => (
              <Link
                key={a.id}
                href={`/app/planning/agents/${a.id}`}
                onClick={() => saveRecent(a)}
                className="inline-flex items-center gap-2 rounded-full border border-[color:var(--app-border)] bg-[color:var(--app-surface)] px-3 py-1.5 text-sm text-[color:var(--app-text)] hover:bg-[color:var(--app-soft)]"
              >
                <span
                  className="inline-flex h-2 w-2 rounded-full"
                  style={{ backgroundColor: "var(--palaj-l)" }}
                />
                {agentLabel(a)}
              </Link>
            ))}
          </div>
        </SectionCard>
      )}

      {/* Results */}
      <SectionCard title="Agents" icon={<User className="h-4 w-4" />}>
        {isLoading ? (
          <div className="text-sm text-[color:var(--app-muted)]">
            Chargement…
          </div>
        ) : (
          <div className="space-y-3">
            {/* Header results + switch */}
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm text-[color:var(--app-muted)]">
                {filtered.length} résultat{filtered.length > 1 ? "s" : ""}
                {query.trim() ? (
                  <>
                    {" "}
                    pour{" "}
                    <span className="font-medium text-[color:var(--app-text)]">
                      “{query.trim()}”
                    </span>
                  </>
                ) : null}
              </div>

              <div className="flex items-center gap-3">
                <div className="text-xs text-[color:var(--app-muted)]">
                  Affichage : {Math.min(50, filtered.length)}/{filtered.length}
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-[color:var(--app-muted)]">
                    Inactifs
                  </span>
                  <ActiveSwitch
                    checked={includeInactive}
                    onToggle={() => setIncludeInactive((v) => !v)}
                    tooltipOn="Masquer les inactifs"
                    tooltipOff="Inclure les inactifs"
                    labelOn="Inactifs inclus"
                    labelOff="Actifs uniquement"
                    showLabel={false}
                  />
                </div>
              </div>
            </div>

            {filtered.length === 0 ? (
              <div className="space-y-1">
                <div className="text-sm font-medium text-[color:var(--app-text)]">
                  Aucun résultat
                </div>
                <div className="text-sm text-[color:var(--app-muted)]">
                  Essaie avec un autre nom/prénom ou un matricule.
                </div>
              </div>
            ) : (
              <div className="grid gap-2 md:grid-cols-2">
                {filtered.slice(0, 50).map((a) => (
                  <Link
                    key={a.id}
                    href={`/app/planning/agents/${a.id}`}
                    onClick={() => {
                      saveRecent(a);
                      setRecents(loadRecents());
                    }}
                    className={[
                      "group flex items-center justify-between gap-3 rounded-xl px-3 py-3",
                      "border border-transparent",
                      "transition hover:-translate-y-0.5 hover:bg-[color:var(--app-soft)] hover:shadow-sm",
                      "hover:ring-1 hover:ring-[color:var(--app-ring)] hover:ring-inset",
                      "focus:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-focus)]",
                    ].join(" ")}
                  >
                    <div className="flex min-w-0 items-center gap-3">
                      {/* Avatar initials */}
                      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[color:var(--app-soft)] text-[color:var(--app-soft-text)] ring-1 ring-[color:var(--app-border)]">
                        <span className="text-xs font-semibold">
                          {initials(a)}
                        </span>
                      </div>

                      <div className="min-w-0">
                        <div className="flex items-center gap-2 truncate">
                          <span className="truncate text-sm font-semibold text-[color:var(--app-text)]">
                            {agentLabel(a)}
                          </span>

                          {a.actif === false && (
                            <span className="inline-flex shrink-0 items-center rounded-full border border-[color:var(--app-border)] px-2 py-0.5 text-[11px] font-medium text-[color:var(--app-muted)]">
                              Inactif
                            </span>
                          )}
                        </div>

                        {formatMeta(a) && (
                          <div className="truncate text-xs text-[color:var(--app-muted)]">
                            {formatMeta(a)}
                          </div>
                        )}
                      </div>
                    </div>

                    <span className="text-sm text-[color:var(--app-muted)] transition group-hover:translate-x-0.5">
                      →
                    </span>
                  </Link>
                ))}
              </div>
            )}

            {filtered.length > 50 && (
              <div className="rounded-lg border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-3 text-xs text-[color:var(--app-muted)]">
                Trop de résultats ({filtered.length}). Affine ta recherche pour
                trouver plus vite.
              </div>
            )}
          </div>
        )}
      </SectionCard>
    </div>
  );
}
