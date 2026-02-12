import type { Key } from "swr";
import { validateAgentRh } from "@/services/rh-validation.service";

export async function rhValidationAgentFetcher(key: Key) {
  const [, , agentId, startDate, endDate] = key as readonly [
    string,
    string,
    number,
    string,
    string,
  ];

  return validateAgentRh({
    agent_id: agentId,
    date_debut: startDate,
    date_fin: endDate,
  });
}
