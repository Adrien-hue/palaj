"use client";

import { useEffect, useMemo, useState } from "react";
import type { ListResponse } from "@/types";

export type ListingState<T> = {
  data: ListResponse<T> | null;
  loading: boolean;
  error: string | null;
  page: number;
  pageSize: number;
  totalPages: number;
  total: number;
  canPrev: boolean;
  canNext: boolean;
  setPage: (p: number) => void;
  setPageSize: (s: number) => void;
  refresh: () => void;
};

export function useListing<T>(opts: {
  fetcher: (args: { page: number; pageSize: number }) => Promise<ListResponse<T>>;
  initialPage?: number;
  initialPageSize?: number;
}): ListingState<T> {
  const { fetcher, initialPage = 1, initialPageSize = 10 } = opts;
  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [data, setData] = useState<ListResponse<T> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [bump, setBump] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetcher({ page, pageSize: pageSize });
        if (!cancelled) setData(res);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Erreur inconnue");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    run();
    return () => {
      cancelled = true;
    };
  }, [fetcher, page, pageSize, bump]);

  useEffect(() => {
    if (!data) return;
    if (page > (data.meta.pages || 1)) setPage(data.meta.pages || 1);
  }, [data, page]);

  const totalPages = data?.meta.pages ?? 1;
  const total = data?.meta.total ?? 0;

  const canPrev = page > 1;
  const canNext = page < totalPages;

  function refresh() {
    setBump((x) => x + 1);
  }

  // si l’utilisateur change pageSize, on revient page 1 (standard UX)
  function setPageSizeSafe(s: number) {
    setPage(1);
    setPageSize(s);
  }

  return {
    data,
    loading,
    error,
    page,
    pageSize,
    totalPages,
    total,
    canPrev,
    canNext,
    setPage,
    setPageSize: setPageSizeSafe,
    refresh,
  };
}