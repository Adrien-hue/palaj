import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";
import { RhPosteDayRequest, RhPosteDayResponse, RhPosteSummaryRequest, RhPosteSummaryResponse } from "@/types";
import type { RhValidateAgentRequest, RhValidateAgentResponse, RhValidateTeamRequest, RhValidateTeamResponse } from "@/types/rhValidation";

export async function validateAgentRh(payload: RhValidateAgentRequest): Promise<RhValidateAgentResponse> {
  return apiFetch<RhValidateAgentResponse>(backendPath("/rh/validate/agent"), {
    body: payload,
  });
}

export async function validateTeamRh(params: {
  request: RhValidateTeamRequest;
  profile: "fast" | "full";
  signal?: AbortSignal;
}): Promise<RhValidateTeamResponse> {
  const { request, profile, signal } = params;

  return apiFetch<RhValidateTeamResponse>(backendPath(`/rh/validate/team?profile=${profile}`), {
    method: "POST",
    body: request,
    signal,
  });
}

export async function validatePosteRhDay(args: {
  request: RhPosteDayRequest;
  profile: "fast" | "full";
  include_info?: boolean;
}): Promise<RhPosteDayResponse> {
  const { request, profile, include_info = false } = args;

  return apiFetch(backendPath(`/rh/validate/poste/day?profile=${profile}&include_info=${include_info}`), {
    method: "POST",
    body: request,
  });
}

export async function getRhPosteSummary(params: {
  profile: string;
  body: RhPosteSummaryRequest;
  signal?: AbortSignal;
}): Promise<RhPosteSummaryResponse> {
  const { profile, body, signal } = params;
  return apiFetch<RhPosteSummaryResponse>(backendPath(`/rh/validate/poste/summary?profile=${encodeURIComponent(profile)}`), {
    method: "POST",
    body,
    signal,
  });
}