"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import type { Poste } from "@/types/postes";
import { RecentCombobox } from "@/components/pickers/RecentCombobox";

const RECENTS_KEY = "palaj.recents.postes";

function posteLabel(p: Poste) {
  return p.nom ?? `Poste #${p.id}`;
}

function normalize(s: string) {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "");
}

function searchValue(p: Poste) {
  return normalize(`${p.nom ?? ""} ${p.id ?? ""}`);
}

function LeadingPoste({ p }: { p: Poste }) {
  return (
    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[color:var(--app-soft)] ring-1 ring-[color:var(--app-border)]">
      <span className="text-[11px] font-semibold text-[color:var(--app-soft-text)]">
        {posteLabel(p).slice(0, 2).toUpperCase()}
      </span>
    </span>
  );
}

export function PostePicker({
  postes,
  isLoading,
  selectedId,
  onPick,
}: {
  postes: Poste[];
  isLoading?: boolean;
  selectedId?: number | null;
  onPick?: (poste: Poste) => void;
}) {
  const router = useRouter();

  return (
    <div className="space-y-3">
      <div className="text-sm text-[color:var(--app-muted)]">
        {postes.length} poste{postes.length > 1 ? "s" : ""}
      </div>

      <RecentCombobox<Poste>
        items={postes}
        storageKey={RECENTS_KEY}
        selectedId={selectedId ?? null}
        placeholder="Sélectionner un poste…"
        searchPlaceholder="Rechercher… (nom du poste)"
        recentsLabel="Récemment consultés"
        listLabel="Postes"
        emptyLabel={isLoading ? "Chargement…" : "Aucun résultat."}
        getId={(p) => p.id}
        getSearchValue={(p) => searchValue(p)}
        renderLeading={(p) => <LeadingPoste p={p} />}
        renderTitle={(p) => posteLabel(p)}
        renderSubtitle={(p) => `ID: ${p.id}`}
        onPick={(p) => {
          if (onPick) return onPick(p);
          router.push(`/app/planning/postes/${p.id}`);
        }}
        disabled={isLoading}
      />

      <div className="text-xs text-[color:var(--app-muted)]">
        Astuce : tape un nom de poste pour filtrer rapidement.
      </div>
    </div>
  );
}
