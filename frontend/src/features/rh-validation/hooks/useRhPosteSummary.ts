import useSWR from "swr";
import { buildRhPosteSummaryVm } from "../vm/rhPosteSummary.vm";
import { rhValidationPosteSummaryKey } from "../swr/rhValidation.key";
import { rhValidationPosteSummaryFetcher } from "../swr/rhValidation.fetcher";

import type { RhPosteSummaryResponse } from "@/types";
import type { RhPosteSummaryVm } from "../vm/rhPosteSummary.vm";

export function useRhPosteSummary(params: {
  posteId: number | null;
  startDate: string | null;
  endDate: string | null;
  profile: string | null;
  enabled?: boolean;
}) {
  const key =
    params.enabled === false
      ? null
      : rhValidationPosteSummaryKey(params.posteId, params.startDate, params.endDate, params.profile);

  const swr = useSWR<RhPosteSummaryResponse>(key, rhValidationPosteSummaryFetcher);

  const vm: RhPosteSummaryVm | undefined = swr.data
    ? buildRhPosteSummaryVm(swr.data)
    : undefined;

  return {
    ...swr,
    vm,
  };
}
