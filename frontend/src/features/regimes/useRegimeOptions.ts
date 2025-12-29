"use client";

import { useEffect, useMemo, useState } from "react";
import { listRegimes } from "@/services/regimes.service";
import type { Regime } from "@/types";
import type { SelectOption } from "@/components/ui/forms/SelectField";

export function useRegimeOptions(opts?: { includeNone?: boolean }) {
  const includeNone = opts?.includeNone ?? true;

  const [regimes, setRegimes] = useState<Regime[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      setLoading(true);
      setError(null);
      try {
        const res = await listRegimes({ page: 1, page_size: 200 });
        if (!cancelled) setRegimes(res.items);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Erreur chargement régimes");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    run();
    return () => {
      cancelled = true;
    };
  }, []);

  const options: SelectOption[] = useMemo(() => {
    const base = regimes.map((r) => ({ value: String(r.id), label: r.nom }));
    return includeNone ? [{ value: "", label: "Aucun régime" }, ...base] : base;
  }, [includeNone, regimes]);

  return { options, loading, error };
}
