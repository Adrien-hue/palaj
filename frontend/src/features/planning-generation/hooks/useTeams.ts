"use client";

import useSWR from "swr";

import { listTeams } from "@/services/teams.service";
import type { Team } from "@/types";

export function useTeams() {
  return useSWR<Team[], Error>(["planningGeneration", "teams"], async () => {
    const response = await listTeams({ page: 1, page_size: 200 });
    return response.items;
  });
}
