import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";
import type { RhValidateAgentRequest, RhValidateAgentResponse } from "@/types/rhValidation";

export async function validateAgentRh(payload: RhValidateAgentRequest): Promise<RhValidateAgentResponse> {
  return apiFetch<RhValidateAgentResponse>(backendPath("/rh/validate/agent"), {
    body: payload,
  });
}
