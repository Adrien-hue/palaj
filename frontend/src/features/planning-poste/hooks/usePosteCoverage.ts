"use client";

import useSWR from "swr";
import { getPosteCoverage } from "@/services/poste-coverage.service";
import type { PosteCoverageDto } from "@/types/posteCoverage";

type Params = { posteId: number | null };
type Key = readonly ["posteCoverage", number];

function keyOf(p: Params): Key | null {
  if (!p.posteId) return null;
  return ["posteCoverage", p.posteId];
}

export function usePosteCoverage(p: Params) {
  return useSWR<PosteCoverageDto, Error, Key | null>(
    keyOf(p),
    ([, posteId]) => getPosteCoverage(posteId),
    {
      revalidateOnFocus: false,
      keepPreviousData: true,
    }
  );
}
