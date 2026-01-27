"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Plus, Trash2, X } from "lucide-react";

import { useConfirm } from "@/hooks/useConfirm";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

type Id = number;

function byLabel(a: string, b: string) {
  return a.localeCompare(b, "fr", { sensitivity: "base" });
}

export function AssociationCard<TItem, TLink>({
  title,
  entityName,
  linkedCountLabel,
  emptyText,

  loadAllItems,
  searchLinks,

  getItemId,
  getItemLabel,

  getLinkItemId,

  addLink,
  removeLink,
}: {
  // UI
  title: string;
  entityName: string; // ex: "équipe GM" ou "agent Dupont"
  linkedCountLabel?: (count: number) => string;
  emptyText: string;

  // data loaders
  loadAllItems: () => Promise<TItem[]>;
  searchLinks: () => Promise<TLink[]>;

  // item accessors
  getItemId: (item: TItem) => Id;
  getItemLabel: (item: TItem) => string;

  // link accessor (extract the "other side" id)
  getLinkItemId: (link: TLink) => Id;

  // mutations
  addLink: (itemId: Id) => Promise<void>;
  removeLink: (itemId: Id) => Promise<void>;
}) {
  const { confirm, ConfirmDialog } = useConfirm();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [items, setItems] = useState<TItem[]>([]);
  const [links, setLinks] = useState<TLink[]>([]);

  const [adding, setAdding] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<Id | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadItemsOnce = useCallback(async () => {
    try {
      const all = await loadAllItems();
      setItems(all);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur inconnue");
    }
  }, [loadAllItems]);

  const refreshLinks = useCallback(async () => {
    try {
      const res = await searchLinks();
      setLinks(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur inconnue");
    }
  }, [searchLinks]);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      setLoading(true);
      setError(null);
      try {
        await Promise.all([loadItemsOnce(), refreshLinks()]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    run();
    return () => {
      cancelled = true;
    };
  }, [loadItemsOnce, refreshLinks]);

  const linkedIds = useMemo(() => new Set(links.map(getLinkItemId)), [links, getLinkItemId]);

  const linkedItems = useMemo(() => {
    const map = new Map(items.map((i) => [getItemId(i), i]));
    const arr = links
      .map((l) => map.get(getLinkItemId(l)))
      .filter((x): x is TItem => x != null);

    arr.sort((a, b) => byLabel(getItemLabel(a), getItemLabel(b)));
    return arr;
  }, [items, links, getItemId, getItemLabel, getLinkItemId]);

  const candidates = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items
      .filter((i) => !linkedIds.has(getItemId(i)))
      .filter((i) => {
        if (!q) return true;
        return getItemLabel(i).toLowerCase().includes(q) || String(getItemId(i)).includes(q);
      })
      .sort((a, b) => byLabel(getItemLabel(a), getItemLabel(b)))
      .slice(0, 20);
  }, [items, linkedIds, query, getItemId, getItemLabel]);

  const headerCount = linkedCountLabel ? linkedCountLabel(linkedItems.length) : String(linkedItems.length);

  const handleAdd = useCallback(async () => {
    if (!selectedId) return;

    setSubmitting(true);
    try {
      await addLink(selectedId);
      toast.success("Ajout effectué");
      setAdding(false);
      setQuery("");
      setSelectedId(null);
      await refreshLinks();
    } catch (e) {
      toast.error("Ajout impossible", {
        description: e instanceof Error ? e.message : "Erreur inconnue",
      });
    } finally {
      setSubmitting(false);
    }
  }, [selectedId, addLink, refreshLinks]);

  const handleRemove = useCallback(
    async (item: TItem) => {
      const id = getItemId(item);

      const ok = await confirm({
        title: "Retirer",
        description: `Confirmer le retrait de "${getItemLabel(item)}" (${entityName}) ?`,
        confirmText: "Retirer",
        cancelText: "Annuler",
        variant: "danger",
      });
      if (!ok) return;

      setSubmitting(true);
      try {
        await removeLink(id);
        toast.success("Retrait effectué");
        await refreshLinks();
      } catch (e) {
        toast.error("Retrait impossible", {
          description: e instanceof Error ? e.message : "Erreur inconnue",
        });
      } finally {
        setSubmitting(false);
      }
    },
    [confirm, entityName, getItemId, getItemLabel, removeLink, refreshLinks]
  );

  return (
    <>
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between gap-3">
            <CardTitle className="text-sm">
              {title}
              <span className="ml-2 text-xs text-muted-foreground">{headerCount}</span>
            </CardTitle>

            <div className="flex items-center gap-2">
              {!adding ? (
                <Button size="sm" onClick={() => setAdding(true)} disabled={loading || !!error}>
                  <Plus className="mr-2 h-4 w-4" />
                  Ajouter
                </Button>
              ) : (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setAdding(false);
                    setQuery("");
                    setSelectedId(null);
                  }}
                  disabled={submitting}
                >
                  <X className="mr-2 h-4 w-4" />
                  Annuler
                </Button>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-3">
          {adding ? (
            <div className="space-y-2 rounded-xl border bg-muted/30 p-3">
              <div className="text-sm font-medium">Ajouter</div>

              <Input
                value={query}
                onChange={(e) => setQuery(e.currentTarget.value)}
                placeholder="Rechercher…"
                disabled={submitting}
              />

              <div className="max-h-56 overflow-auto rounded-lg border bg-background">
                {candidates.length === 0 ? (
                  <div className="p-3 text-sm text-muted-foreground">Aucun résultat.</div>
                ) : (
                  candidates.map((i) => {
                    const id = getItemId(i);
                    const selected = selectedId === id;
                    return (
                      <button
                        key={id}
                        type="button"
                        className={[
                          "w-full text-left px-3 py-2 text-sm hover:bg-muted",
                          selected ? "bg-muted" : "",
                        ].join(" ")}
                        onClick={() => setSelectedId(id)}
                        disabled={submitting}
                      >
                        <div className="font-medium truncate">{getItemLabel(i)}</div>
                        <div className="text-xs text-muted-foreground truncate">#{id}</div>
                      </button>
                    );
                  })
                )}
              </div>

              <div className="flex justify-end">
                <Button onClick={handleAdd} disabled={!selectedId || submitting}>
                  Ajouter
                </Button>
              </div>
            </div>
          ) : null}

          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : error ? (
            <div className="text-sm text-destructive">{error}</div>
          ) : linkedItems.length === 0 ? (
            <div className="text-sm text-muted-foreground">{emptyText}</div>
          ) : (
            <div className="space-y-2">
              {linkedItems.map((i) => {
                const id = getItemId(i);
                return (
                  <div
                    key={id}
                    className="flex items-center justify-between gap-3 rounded-lg border bg-muted/40 px-3 py-2"
                  >
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium">{getItemLabel(i)}</div>
                      <div className="text-xs text-muted-foreground">#{id}</div>
                    </div>

                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label="Retirer"
                      onClick={() => void handleRemove(i)}
                      disabled={submitting}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <ConfirmDialog />
    </>
  );
}
