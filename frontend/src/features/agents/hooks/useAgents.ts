"use client";

import useSWR from "swr";
import type { Agent } from "@/types";
import { listAllAgents } from "@/services/agents.service";

export function useAgents() {
  return useSWR<Agent[], Error>(["agents", "all"], () => listAllAgents(), {
    revalidateOnFocus: false,
    keepPreviousData: true,
  });
}
