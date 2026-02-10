"use client";

import type { PosteDetail } from "@/types";
import { getPoste } from "@/services/postes.service";
import type { SWRConfiguration } from "swr";

/** ===== Single ===== */
export type PosteKey = readonly ["poste", number];

export function posteKey(id: number): PosteKey {
  return ["poste", id] as const;
}

export async function fetchPoste([, id]: PosteKey): Promise<PosteDetail> {
  return getPoste(id);
}

export const posteSWRConfig: SWRConfiguration = {
  revalidateOnFocus: false,
  dedupingInterval: 30_000,
};

/** ===== Batch by ids ===== */
export type PostesByIdsKey = readonly ["postes", "byIds", string];

export function normalizePosteIds(ids: number[]) {
  return Array.from(new Set(ids)).sort((a, b) => a - b);
}

export function postesByIdsKey(ids: number[]): PostesByIdsKey | null {
  const norm = normalizePosteIds(ids);
  if (norm.length === 0) return null;
  return ["postes", "byIds", norm.join(",")] as const;
}

export async function fetchPostesByIds([, , idsKey]: PostesByIdsKey): Promise<PosteDetail[]> {
  if (!idsKey) return [];
  const ids = idsKey.split(",").map(Number);
  return Promise.all(ids.map((id) => getPoste(id)));
}
