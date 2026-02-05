"use client";

import * as React from "react";
import { toast } from "sonner";

import type { PostePlanning, PostePlanningDay, PostePlanningDayPutBody } from "@/types";
import { putPostePlanningDay, deletePostePlanningDay } from "@/services/poste-planning.service";
import {
  optimisticApplyPostePlanningDay,
  applyServerDay,
  optimisticRemoveDay,
} from "@/features/planning-poste/utils/postePlanning.optimistic";

function errorMessage(e: unknown) {
  if (e instanceof Error) return e.message;
  if (typeof e === "string") return e;
  return "Une erreur est survenue.";
}

export function usePostePlanningActions(args: {
  posteId: number | null;
  mutatePlanning: (
    data?:
      | PostePlanning
      | Promise<PostePlanning | undefined>
      | ((current: PostePlanning | undefined) => PostePlanning | undefined),
    opts?: { revalidate?: boolean }
  ) => Promise<any>;
}) {
  const { posteId, mutatePlanning } = args;

  const [isSaving, setIsSaving] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);

  const saveDay = React.useCallback(
    async (p: {
      dayDate: string;
      day_type: string;
      description: string | null;
      body: PostePlanningDayPutBody;
    }): Promise<PostePlanningDay> => {
      if (!posteId) throw new Error("posteId is required");

      setIsSaving(true);
      let snapshot: PostePlanning | undefined;

      try {
        // optimistic
        await mutatePlanning(
          (curr) => {
            snapshot = curr;
            return optimisticApplyPostePlanningDay(curr, {
              dayDate: p.dayDate,
              day_type: p.day_type,
              description: p.description,
              body: p.body,
            } as any);
          },
          { revalidate: false }
        );

        // server
        const serverDay = await putPostePlanningDay(posteId, p.dayDate, p.body);

        // apply server result
        await mutatePlanning((curr) => applyServerDay(curr, serverDay), {
          revalidate: false,
        });

        // revalidate
        await mutatePlanning(undefined as any, { revalidate: true });

        toast.success("Planning mis à jour", {
          description: `Modifications enregistrées pour le ${p.dayDate}.`,
        });

        return serverDay;
      } catch (e) {
        await mutatePlanning(snapshot, { revalidate: false });

        toast.error("Échec de l’enregistrement", {
          description: errorMessage(e),
        });

        throw e;
      } finally {
        setIsSaving(false);
      }
    },
    [posteId, mutatePlanning]
  );

  const deleteDay = React.useCallback(
    async (dayDate: string) => {
      if (!posteId) throw new Error("posteId is required");

      setIsDeleting(true);
      let snapshot: PostePlanning | undefined;

      try {
        // optimistic remove
        await mutatePlanning(
          (curr) => {
            snapshot = curr;
            return optimisticRemoveDay(curr, dayDate);
          },
          { revalidate: false }
        );

        // server
        await deletePostePlanningDay(posteId, dayDate);

        // revalidate
        await mutatePlanning(undefined as any, { revalidate: true });

        toast.success("Jour supprimé", {
          description: `Suppression confirmée pour le ${dayDate}.`,
        });
      } catch (e) {
        await mutatePlanning(snapshot, { revalidate: false });

        toast.error("Échec de la suppression", {
          description: errorMessage(e),
        });

        throw e;
      } finally {
        setIsDeleting(false);
      }
    },
    [posteId, mutatePlanning]
  );

  return { saveDay, deleteDay, isSaving, isDeleting };
}
