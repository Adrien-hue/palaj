import { apiFetch } from "@/lib/api";
import type { CreateQualificationBody, Qualification, SearchQualificationsParams, UpdateQualificationBody } from "@/types";

export async function createQualification(body: CreateQualificationBody) {
    return apiFetch<Qualification>("/qualifications", {
        method: "POST",
        body: body,
    });
}

export async function deleteQualification(agentId: number, posteId: number) {
    return apiFetch<Qualification>(`/qualifications/${agentId}/${posteId}`, {
        method: "DELETE",
    });
}

export async function searchQualifications(params?: SearchQualificationsParams) {
    const search = new URLSearchParams();
    if (params?.agent_id !== undefined && params?.agent_id !== null) {
        search.set("agent_id", String(params.agent_id));
    }
    if (params?.poste_id !== undefined && params?.poste_id !== null) {
        search.set("poste_id", String(params.poste_id));
    }

    const qs = search.toString();
    return apiFetch<Qualification[]>(`/qualifications?${qs}`);
}

export async function updateQualification(
    agentId: number,
    posteId: number,
    payload: UpdateQualificationBody
) {
    return apiFetch<Qualification>(`/qualifications/${agentId}/${posteId}`, {
        method: "PATCH",
        body: payload,
    });
}