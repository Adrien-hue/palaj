// frontend/src/components/admin/QualificationCard/helpers.ts
import type { Qualification } from "@/types";
import type { QualificationMode } from "./types"; 

export function todayYYYYMMDD() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export function formatFR(yyyyMMdd?: string | null) {
  if (!yyyyMMdd) return "—";
  const [y, m, d] = yyyyMMdd.split("-");
  if (!y || !m || !d) return yyyyMMdd;
  return `${d}/${m}/${y}`;
}

export function sortByLabelFR<T extends { label: string }>(arr: T[]) {
  return arr.sort((a, b) => a.label.localeCompare(b.label, "fr"));
}

/**
 * On Agent details: we manage qualifications for Postes (related_id = poste_id)
 * On Poste details: we manage qualifications for Agents (related_id = agent_id)
 */
export function getRelatedId(mode: QualificationMode, q: Qualification) {
  return mode === "agent" ? q.poste_id : q.agent_id;
}
