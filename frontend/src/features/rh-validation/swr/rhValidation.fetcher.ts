import type { Key } from "swr";
import { getRhPosteSummary, validateAgentRh, validateTeamRh } from "@/services/rh-validation.service";

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


export async function rhValidationPosteSummaryFetcher(key: Key) {
  const [, , , posteId, startDate, endDate, profile] = key as readonly [
    "rh-validation",
    "poste",
    "summary",
    number,
    string,
    string,
    string,
  ];

  return getRhPosteSummary({
    profile,
    body: {
      poste_id: posteId,
      date_debut: startDate,
      date_fin: endDate,
    },
  });
}

export async function rhValidationTeamFetcher(key: Key) {
  const [, , teamId, startDate, endDate, profile] = key as readonly [
    "rh-validation",
    "team",
    number,
    string,
    string,
    "fast" | "full",
  ];

  return validateTeamRh({
    profile,
    request: {
      team_id: teamId,
      date_debut: startDate,
      date_fin: endDate,
    },
  });
}
