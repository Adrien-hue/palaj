import type { Key } from "swr";
import { validatePosteRhDay } from "@/services/rh-validation.service";

export async function rhValidationPosteDayFetcher(key: Key) {
  const [, , , posteId, day, startDate, endDate, profile, includeInfo] = key as readonly [
    string,
    string,
    string,
    number,
    string,
    string,
    string,
    "fast" | "full",
    boolean,
  ];

  return validatePosteRhDay({
    request: {
      poste_id: posteId,
      day,
      date_debut: startDate,
      date_fin: endDate,
    },
    profile,
    include_info: includeInfo,
  });
}
