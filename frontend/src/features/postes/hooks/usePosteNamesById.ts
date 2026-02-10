"use client";

import { useEffect, useMemo } from "react";
import useSWR, { useSWRConfig } from "swr";
import type { PosteDetail } from "@/types";
import {
  fetchPostesByIds,
  posteKey,
  posteSWRConfig,
  postesByIdsKey,
} from "@/features/postes/swr/poste.swr";

export function usePosteNamesById(posteIds: number[]) {
  const key = useMemo(() => postesByIdsKey(posteIds), [posteIds]);

  const { data, error, isLoading } = useSWR<PosteDetail[]>(
    key,
    fetchPostesByIds,
    posteSWRConfig
  );

  const { mutate } = useSWRConfig();
  useEffect(() => {
    if (!data?.length) return;
    for (const p of data) {
      mutate(posteKey(p.id), p, false);
    }
  }, [data, mutate]);

  const posteNameById = useMemo(() => {
    const m = new Map<number, string>();
    for (const p of data ?? []) m.set(p.id, p.nom);
    return m;
  }, [data]);

  return { posteNameById, isLoading, error };
}
