"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Loader2, Info } from "lucide-react";
import { toast } from "sonner";

import type {
  PosteCoveragePutDto,
  PosteCoverageRequirement,
  Tranche,
} from "@/types";
import {
  getPosteCoverage,
  putPosteCoverage,
} from "@/services/poste-coverage.service";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const WEEKDAYS: Array<{ value: number; label: string }> = [
  { value: 0, label: "Lun" },
  { value: 1, label: "Mar" },
  { value: 2, label: "Mer" },
  { value: 3, label: "Jeu" },
  { value: 4, label: "Ven" },
  { value: 5, label: "Sam" },
  { value: 6, label: "Dim" },
];

function mkKey(weekday: number, trancheId: number) {
  return `${weekday}:${trancheId}`;
}

function clampInt(n: number) {
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.trunc(n));
}

function hhmm(value?: string) {
  if (!value) return "";
  const m = value.match(/(\d{2}:\d{2})/);
  return m?.[1] ?? value.slice(0, 5);
}

export function PosteCoverageCard({
  posteId,
  tranches,
  disabled = false,
}: {
  posteId: number;
  tranches: Tranche[];
  disabled?: boolean;
}) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [initial, setInitial] = useState<PosteCoveragePutDto | null>(null);
  const [draft, setDraft] = useState<PosteCoveragePutDto | null>(null);

  // refs pour navigation clavier (Enter -> next cell)
  const cellRefs = useRef<Record<string, HTMLInputElement | null>>({});

  const reqMap = useMemo(() => {
    const map = new Map<string, number>();
    if (!draft) return map;
    for (const r of draft.requirements) {
      map.set(mkKey(r.weekday, r.tranche_id), r.required_count);
    }
    return map;
  }, [draft]);

  const isDirty = useMemo(() => {
    if (!initial || !draft) return false;
    return JSON.stringify(initial) !== JSON.stringify(draft);
  }, [initial, draft]);

  const totalsByDay = useMemo(() => {
    const totals = new Map<number, number>();
    for (const d of WEEKDAYS) totals.set(d.value, 0);

    for (const d of WEEKDAYS) {
      let sum = 0;
      for (const t of tranches) {
        sum += reqMap.get(mkKey(d.value, t.id)) ?? 0;
      }
      totals.set(d.value, sum);
    }
    return totals;
  }, [reqMap, tranches]);

  const totalsByTranche = useMemo(() => {
    const totals = new Map<number, number>();
    for (const t of tranches) totals.set(t.id, 0);

    for (const t of tranches) {
      let sum = 0;
      for (const d of WEEKDAYS) {
        sum += reqMap.get(mkKey(d.value, t.id)) ?? 0;
      }
      totals.set(t.id, sum);
    }
    return totals;
  }, [reqMap, tranches]);

  const totalWeek = useMemo(() => {
    let sum = 0;
    for (const d of WEEKDAYS) sum += totalsByDay.get(d.value) ?? 0;
    return sum;
  }, [totalsByDay]);

  useEffect(() => {
    let mounted = true;

    setLoading(true);
    setError(null);

    getPosteCoverage(posteId)
      .then((data) => {
        if (!mounted) return;
        const base: PosteCoveragePutDto = {
          poste_id: data.poste_id,
          requirements: data.requirements ?? [],
        };
        setInitial(base);
        setDraft(structuredClone(base));
      })
      .catch((e) => {
        if (!mounted) return;
        setError(e instanceof Error ? e.message : "Erreur inconnue");
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [posteId]);

  function setRequiredCount(weekday: number, trancheId: number, value: number) {
    setDraft((prev) => {
      if (!prev) return prev;

      const next: PosteCoverageRequirement[] = prev.requirements.filter(
        (r) => !(r.weekday === weekday && r.tranche_id === trancheId),
      );

      const v = clampInt(value);
      if (v > 0)
        next.push({ weekday, tranche_id: trancheId, required_count: v });

      return { ...prev, requirements: next };
    });
  }

  function focusNextCell(weekday: number, trancheId: number) {
    const trancheIdx = tranches.findIndex((t) => t.id === trancheId);
    if (trancheIdx < 0) return;

    const next = tranches[trancheIdx + 1];
    if (!next) return;

    const key = mkKey(weekday, next.id);
    cellRefs.current[key]?.focus();
    cellRefs.current[key]?.select?.();
  }

  async function save() {
    if (!draft) return;

    setSaving(true);
    setError(null);

    try {
      const payload: PosteCoveragePutDto = {
        poste_id: posteId,
        requirements: draft.requirements
          .filter((r) => r.required_count > 0)
          .filter((r) => tranches.some((t) => t.id === r.tranche_id)),
      };

      const saved = await putPosteCoverage(posteId, payload);

      const base: PosteCoveragePutDto = {
        poste_id: saved.poste_id,
        requirements: saved.requirements ?? [],
      };

      setInitial(base);
      setDraft(structuredClone(base));

      toast.success("Couverture enregistrée");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Erreur inconnue";
      setError(msg);
      toast.error("Erreur d’enregistrement", { description: msg });
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-3">
          <CardTitle>Couverture</CardTitle>
          <Skeleton className="h-9 w-32" />
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-40 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!draft) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Couverture</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-destructive">
          Impossible de charger la couverture{error ? ` : ${error}` : "."}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <CardTitle>Couverture</CardTitle>
          {isDirty && <Badge variant="secondary">Modifié</Badge>}
        </div>

        <Button onClick={save} disabled={disabled || saving || !isDirty}>
          {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Enregistrer
        </Button>
      </CardHeader>

      <CardContent className="space-y-4">
        {error && (
          <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {error}
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="text-sm text-muted-foreground">
            Renseigne le <span className="font-medium">nombre requis</span> par
            jour et par tranche.
          </div>

          <div className="text-xs text-muted-foreground">
            Total semaine :{" "}
            <span className="font-medium tabular-nums">{totalWeek}</span>
          </div>
        </div>

        <Separator />

        {tranches.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            Ajoute d’abord des tranches pour pouvoir définir la couverture.
          </div>
        ) : (
          <div className="overflow-auto rounded-md border">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="bg-muted/40">
                  <th className="border-b px-3 py-2 text-left">Jour</th>

                  {tranches.map((t) => (
                    <th
                      key={t.id}
                      className="border-b px-3 py-2 text-left whitespace-nowrap"
                    >
                      <div className="flex items-center gap-2">
                        <div className="font-medium">{t.nom}</div>

                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              type="button"
                              className="inline-flex items-center rounded-sm text-muted-foreground hover:text-foreground"
                              aria-label="Infos tranche"
                            >
                              <Info className="h-4 w-4" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent className="max-w-xs">
                            <div className="text-sm font-medium">{t.nom}</div>
                            <div className="text-xs text-muted-foreground">
                              {hhmm(t.heure_debut)} → {hhmm(t.heure_fin)}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              ID: {t.id}
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      </div>
                    </th>
                  ))}

                  <th className="border-b px-3 py-2 text-right whitespace-nowrap">
                    Total
                  </th>
                </tr>
              </thead>

              <tbody>
                {WEEKDAYS.map((d) => (
                  <tr key={d.value} className="hover:bg-muted/20">
                    <td className="border-b px-3 py-2 font-medium">
                      {d.label}
                    </td>

                    {tranches.map((t) => {
                      const key = mkKey(d.value, t.id);
                      const current = reqMap.get(key) ?? 0;
                      const isZero = current === 0;

                      return (
                        <td key={key} className="border-b px-3 py-2">
                          <Input
                            ref={(el) => {
                              cellRefs.current[key] = el;
                            }}
                            type="number"
                            inputMode="numeric"
                            min={0}
                            value={current}
                            disabled={disabled}
                            onFocus={(e) => e.currentTarget.select()}
                            onChange={(e) =>
                              setRequiredCount(
                                d.value,
                                t.id,
                                Number(e.target.value),
                              )
                            }
                            onKeyDown={(e) => {
                              if (e.key === "Escape") {
                                (e.currentTarget as HTMLInputElement).blur();
                                return;
                              }

                              if (e.key === "Enter") {
                                e.preventDefault();
                                focusNextCell(d.value, t.id);
                                return;
                              }

                              if (
                                e.key === "ArrowUp" ||
                                e.key === "ArrowDown"
                              ) {
                                e.preventDefault();
                                const step = e.shiftKey ? 5 : 1;
                                const next =
                                  e.key === "ArrowUp"
                                    ? current + step
                                    : Math.max(0, current - step);
                                setRequiredCount(d.value, t.id, next);
                              }
                            }}
                            className={[
                              "w-16 text-center tabular-nums",
                              isZero ? "text-muted-foreground" : "font-medium",
                            ].join(" ")}
                          />
                        </td>
                      );
                    })}

                    <td className="border-b px-3 py-2 text-right font-medium tabular-nums">
                      {totalsByDay.get(d.value) ?? 0}
                    </td>
                  </tr>
                ))}

                <tr className="bg-muted/30">
                  <td className="px-3 py-2 text-sm font-medium">Total</td>
                  {tranches.map((t) => (
                    <td
                      key={t.id}
                      className="px-3 py-2 text-center font-medium tabular-nums"
                    >
                      {totalsByTranche.get(t.id) ?? 0}
                    </td>
                  ))}
                  <td className="px-3 py-2 text-right font-medium tabular-nums">
                    {totalWeek}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
