"use client";

import useSWR from "swr";
import { getPostePlanning } from "@/services/planning.service";
import type { PostePlanning } from "@/types/postePlanning";

type Params = {
  posteId: number | null;
  startDate: string;
  endDate: string;
};

type PostePlanningKey = readonly ["postePlanning", number, string, string];

function keyOf(p: Params): PostePlanningKey | null {
  if (!p.posteId) return null;
  return ["postePlanning", p.posteId, p.startDate, p.endDate];
}

export function usePostePlanning(p: Params) {
  return useSWR<PostePlanning, Error, PostePlanningKey | null>(
    keyOf(p),
    ([, posteId, startDate, endDate]) =>
      getPostePlanning(posteId, { startDate, endDate }),
    {
      revalidateOnFocus: false,
      keepPreviousData: true,
    }
  );
}
