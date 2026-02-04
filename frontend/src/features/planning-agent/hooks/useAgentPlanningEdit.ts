"use client";

import { useSWRConfig, type Key, unstable_serialize } from "swr";
import type { AgentPlanning, AgentDayPutDTO } from "@/types";
import {
  putAgentDayPlanning,
  deleteAgentDayPlanning,
} from "@/services/agent-planning.service";

import {
  optimisticApplyDayById,
  optimisticRemoveDay,
  applyServerDay,
} from "@/features/planning-agent/utils/agentPlanning.optimistic";

import { toast } from "sonner";

function hasDaysArray(x: unknown): x is AgentPlanning {
  return !!x && typeof x === "object" && Array.isArray((x as any).days);
}

export function useAgentPlanningEdit(agentId: number, planningKey: Key | null) {
  const { mutate, cache } = useSWRConfig();

  async function saveDay(args: {
    dayDate: string;
    day_type: string;
    description: string | null;
    tranche_id: number | null;
  }) {
    if (!planningKey) return;

    const body: AgentDayPutDTO = {
      day_type: args.day_type,
      description: args.description,
      tranche_id: args.tranche_id,
    };

    const cacheKey = unstable_serialize(planningKey);
    const snapshot = cache.get(cacheKey) as AgentPlanning | undefined;

    // optimistic
    mutate(
      planningKey,
      (current?: AgentPlanning) => {
        if (!hasDaysArray(current)) return current;
        return optimisticApplyDayById(current, args);
      },
      { revalidate: false }
    );

    try {
      const serverDay = await putAgentDayPlanning(agentId, args.dayDate, body);

      // reconcile
      mutate(
        planningKey,
        (current?: AgentPlanning) => {
          if (!hasDaysArray(current)) return current;
          return applyServerDay(current, serverDay);
        },
        { revalidate: false }
      );

      // refetch for full consistency
      mutate(planningKey);

      toast.success("Journée mise à jour", {
        description: "Les modifications ont été enregistrées avec succès.",
      });

      return serverDay;
    } catch (e) {
      mutate(planningKey, snapshot, { revalidate: false });

      toast.error("Erreur lors de l’enregistrement", {
        description:
          e instanceof Error
            ? e.message
            : "Une erreur est survenue lors de la sauvegarde.",
      });

      throw e;
    }
  }

  async function removeDay(dayDate: string) {
    if (!planningKey) return;

    const cacheKey = unstable_serialize(planningKey);
    const snapshot = cache.get(cacheKey) as AgentPlanning | undefined;

    mutate(
      planningKey,
      (current?: AgentPlanning) => {
        if (!hasDaysArray(current)) return current;
        return optimisticRemoveDay(current, dayDate);
      },
      { revalidate: false }
    );

    try {
      await deleteAgentDayPlanning(agentId, dayDate);
      mutate(planningKey);

      toast.success("Journée supprimée", {
        description: "La journée a été supprimée du planning.",
      });
    } catch (e) {
      mutate(planningKey, snapshot, { revalidate: false });

      toast.error("Erreur lors de la suppression", {
        description:
          e instanceof Error
            ? e.message
            : "Impossible de supprimer la journée.",
      });

      throw e;
    }
  }

  return { saveDay, removeDay };
}
