export type Severity = "critical" | "high" | "medium" | "low";
export type IncidentStatus = "received" | "analyzing" | "analyzed" | "failed";

export interface AgentStep {
  id: number;
  step_order: number;
  agent_name: string;
  input_summary: string | null;
  output: string | null;
  latency_ms: number | null;
  status: string;
}

export interface IncidentSummary {
  id: number;
  title: string;
  service_name: string;
  severity: Severity;
  status: IncidentStatus;
  source: string;
  confidence: number | null;
  created_at: string;
  analyzed_at: string | null;
  summary: string | null;
}

export interface IncidentDetail extends IncidentSummary {
  alert_payload: Record<string, unknown>;
  log_snippets: string[];
  metrics_data: Record<string, unknown>;
  log_analysis: string | null;
  metrics_analysis: string | null;
  root_cause: string | null;
  runbook: string | null;
  error_message: string | null;
  agent_steps: AgentStep[];
}

export interface IncidentStats {
  total: number;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  avg_analysis_time_seconds: number | null;
}
