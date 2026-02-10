"use client";

import type { AgentDayPutDTO } from "@/types";
import {
  putAgentDayPlanning,
  deleteAgentDayPlanning,
} from "@/services/agent-planning.service";
import { toast } from "sonner";

export function useAgentDayMutations(agentId: number) {
  async function saveDay(args: {
    dayDate: string;
    day_type: string;
    description: string | null;
    tranche_id: number | null;
  }) {
    const body: AgentDayPutDTO = {
      day_type: args.day_type,
      description: args.description,
      tranche_id: args.tranche_id,
    };

    try {
      const serverDay = await putAgentDayPlanning(agentId, args.dayDate, body);

      toast.success("Journée mise à jour", {
        description: "Les modifications ont été enregistrées avec succès.",
      });

      return serverDay;
    } catch (e) {
      toast.error("Erreur lors de l'enregistrement", {
        description:
          e instanceof Error
            ? e.message
            : "Une erreur est survenue lors de la sauvegarde.",
      });
      throw e;
    }
  }

  async function removeDay(dayDate: string) {
    try {
      await deleteAgentDayPlanning(agentId, dayDate);

      toast.success("Journée supprimée", {
        description: "La journée a été supprimée du planning.",
      });
    } catch (e) {
      toast.error("Erreur lors de la suppression", {
        description:
          e instanceof Error ? e.message : "Impossible de supprimer la journée.",
      });
      throw e;
    }
  }

  return { saveDay, removeDay };
}
