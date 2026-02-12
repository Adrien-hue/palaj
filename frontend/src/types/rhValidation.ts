export type RhViolationSeverity = "info" | "warning" | "error";

export type RhViolation = {
  code: string;
  rule: string;
  severity: RhViolationSeverity;
  message: string;
  start_date?: string; // "YYYY-MM-DD"
  end_date?: string;   // "YYYY-MM-DD"
  start_dt?: string;   // ISO
  end_dt?: string;     // ISO
  meta?: Record<string, unknown>;
};

export type RhValidateAgentRequest = {
  agent_id: number;
  date_debut: string; // "YYYY-MM-DD"
  date_fin: string;   // "YYYY-MM-DD"
};

export type RhValidateAgentResponse = {
  is_valid: boolean;
  violations: RhViolation[];
};
