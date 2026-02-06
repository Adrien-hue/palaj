"use client";

import useSWR from "swr";
import type { Tranche } from "@/types";
import { listTranchesForPoste } from "@/services/tranches.service";

export function usePosteTranches(posteId: number | null) {
  return useSWR<Tranche[], Error>(
    posteId ? ["poste-tranches", posteId] : null,
    () => listTranchesForPoste(posteId!),
    {
      revalidateOnFocus: false,
      keepPreviousData: true,
    }
  );
}
