"use client";

import useSWR from "swr";
import { getPostePlanning } from "@/services/planning.service";
import { PostePlanningKey } from "@/features/planning-poste/hooks/postePlanning.key";
import {
  putPostePlanningDay,
  deletePostePlanningDay,
} from "@/services/poste-planning.service";
import type { PostePlanning, PostePlanningDay, PostePlanningDayPutBody } from "@/types";
import {
  optimisticApplyPostePlanningDay,
  applyServerDay,
  optimisticRemoveDay,
} from "@/features/planning-poste/utils/postePlanning.optimistic";

type Params = {
  posteId: number | null;
  startDate: string;
  endDate: string;
};

function keyOf(p: Params): PostePlanningKey | null {
  if (!p.posteId) return null;
  return ["postePlanning", p.posteId, p.startDate, p.endDate];
}

export function usePostePlanning(p: Params) {
  const swr = useSWR<PostePlanning, Error, PostePlanningKey | null>(
    keyOf(p),
    ([, posteId, startDate, endDate]) =>
      getPostePlanning(posteId, { startDate, endDate }),
    {
      revalidateOnFocus: false,
      keepPreviousData: true,
    }
  );

  const { mutate } = swr;

  async function putDay(args: {
    dayDate: string;
    day_type: string;
    description: string | null;
    body: PostePlanningDayPutBody;
  }): Promise<PostePlanningDay> {
    if (!p.posteId) throw new Error("posteId is required");

    // rollback safe: on prend un snapshot
    const prev = swr.data;

    // optimistic
    await mutate(
      (curr) =>
        optimisticApplyPostePlanningDay(curr, {
          dayDate: args.dayDate,
          day_type: args.day_type,
          description: args.description,
          body: args.body,
        }),
      { revalidate: false }
    );

    try {
      const serverDay = await putPostePlanningDay(p.posteId, args.dayDate, args.body);

      // apply server truth
      await mutate((curr) => applyServerDay(curr, serverDay), {
        revalidate: false,
      });

      // optionnel: revalidate global si vous avez des agrégats/couverture
      await mutate();

      return serverDay;
    } catch (e) {
      // rollback
      await mutate(prev, { revalidate: false });
      throw e;
    }
  }

  async function deleteDay(dayDate: string): Promise<void> {
    if (!p.posteId) throw new Error("posteId is required");

    const prev = swr.data;

    await mutate((curr) => optimisticRemoveDay(curr, dayDate), {
      revalidate: false,
    });

    try {
      await deletePostePlanningDay(p.posteId, dayDate);
      await mutate();
    } catch (e) {
      await mutate(prev, { revalidate: false });
      throw e;
    }
  }

  return {
    ...swr,
    putDay,
    deleteDay,
  };
}
