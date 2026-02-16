import useSWR from "swr";
import type { RhPosteDayResponse } from "@/types";
import { rhValidationPosteDayKey } from "@/features/rh-validation/swr/rhPosteDay.key";
import { rhValidationPosteDayFetcher } from "@/features/rh-validation/swr/rhPosteDay.fetcher";

export function useRhPosteDay(args: {
  posteId: number | null;
  day: string | null;
  startDate: string | null;
  endDate: string | null;
  profile: "fast" | "full";
  includeInfo?: boolean;
  enabled?: boolean;
}) {
  const { posteId, day, startDate, endDate, profile, includeInfo = false, enabled = true } = args;

  const key = enabled
    ? rhValidationPosteDayKey(posteId, day, startDate, endDate, profile, includeInfo)
    : null;

  const swr = useSWR<RhPosteDayResponse>(key, rhValidationPosteDayFetcher, {
    keepPreviousData: true,
  });

  return swr;
}
