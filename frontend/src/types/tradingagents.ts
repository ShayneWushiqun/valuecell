export type TradingAgentsAnalyst =
  | "market"
  | "social"
  | "news"
  | "fundamentals";

export type TradingAgentsRunRequest = {
  symbol: string;
  trade_date: string;
  provider: string;
  deep_model: string;
  quick_model: string;
  output_language: string;
  analysts: TradingAgentsAnalyst[];
  debug: boolean;
};

export type TradingAgentsSummary = {
  technical: string;
  fundamentals: string;
  sentiment: string;
  capital_flow: string;
  final_decision: string;
};

export type TradingAgentsReport = {
  key: string;
  title: string;
  content: string;
};

export type TradingAgentsStepLog = {
  stage: string;
  title: string;
  message: string;
  level: "info" | "running" | "completed" | "warning" | "error";
  progress_percent: number | null;
  created_at: string;
};

export type TradingAgentsRunResult = {
  run_id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  symbol: string;
  trade_date: string;
  provider: string;
  deep_model: string;
  quick_model: string;
  output_language: string;
  analysts: TradingAgentsAnalyst[];
  debug: boolean;
  progress_stage: string | null;
  progress_message: string | null;
  progress_percent: number | null;
  decision_signal: string | null;
  summary: TradingAgentsSummary | null;
  reports: TradingAgentsReport[];
  step_logs: TradingAgentsStepLog[];
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type TradingAgentsRunList = {
  runs: TradingAgentsRunResult[];
  total: number;
  running_count: number;
};
