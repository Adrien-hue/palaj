import { apiFetch } from "@/lib/api/universal";
import { backendPath } from "@/lib/backendPath";
import type { ListParams, ListResponse } from "@/types/api";
import type { Agent, AgentDetails, CreateAgentBody, PatchAgentBody } from "@/types";

export async function activateAgent(id: number) {
  return apiFetch<void>(backendPath(`/agents/${id}/activate`), { method: "PATCH" });
}

export async function createAgent(body: CreateAgentBody) {
  const payload: CreateAgentBody = { actif: true, ...body };
  return apiFetch<Agent>(backendPath("/agents"), { method: "POST", body: payload });
}

export async function deactivateAgent(id: number) {
  return apiFetch<void>(backendPath(`/agents/${id}/deactivate`), { method: "PATCH" });
}

export async function getAgent(id: number) {
  return apiFetch<AgentDetails>(backendPath(`/agents/${id}`));
}

export async function listAgents(params: ListParams = { page: 1, page_size: 20 }) {
  const search = new URLSearchParams();
  if (params.page != null) search.set("page", String(params.page));
  if (params.page_size != null) search.set("page_size", String(params.page_size));

  const qs = search.toString();
  return apiFetch<ListResponse<Agent>>(backendPath(`/agents${qs ? `?${qs}` : ""}`));
}

export async function listAllAgents(params: ListParams = { page: 1, page_size: 200 }): Promise<Agent[]> {
  const res = await listAgents(params);
  return res.items;
}

export async function removeAgent(id: number) {
  return apiFetch<void>(backendPath(`/agents/${id}`), { method: "DELETE" });
}

export async function patchAgent(agentId: number, body: PatchAgentBody) {
  return apiFetch<Agent>(backendPath(`/agents/${agentId}`), { method: "PATCH", body });
}
