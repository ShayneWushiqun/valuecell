import type { AShareDecisionContext } from "@/types/ashare-decision-context";

export type AShareDecisionJudgePayload = {
  ticker: string;
  enable_agent?: boolean;
  force_refresh_context?: boolean;
  user_note?: string | null;
};

export type AShareDecisionJudgeResult = {
  generated_at: string;
  ticker: string;
  available: boolean;
  mode: "rule_fallback" | "agent" | "agent_fallback";
  agent_enabled: boolean;
  agent_unavailable_reason: string | null;
  action: string;
  confidence: number;
  summary: string;
  thesis: string;
  evidence: string[];
  disagreement: string[];
  missing_confirmations: string[];
  invalid_conditions: string[];
  risk_controls: string[];
  time_horizon: string;
  context_snapshot: AShareDecisionContext | Record<string, unknown>;
  raw_agent_output: string | null;
  empty_message: string | null;
};
