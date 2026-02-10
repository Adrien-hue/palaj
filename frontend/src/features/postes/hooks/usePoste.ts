"use client";

import useSWR from "swr";
import type { PosteDetail } from "@/types";
import { fetchPoste, posteKey, posteSWRConfig } from "@/features/postes/swr/poste.swr";

export function usePoste(id: number | null | undefined) {
  const key = id ? posteKey(id) : null;

  const { data, error, isLoading, mutate } = useSWR<PosteDetail>(
    key,
    fetchPoste,
    posteSWRConfig
  );

  return { poste: data, error, isLoading, mutate };
}
