export type HoldingExitSignal = {
  generated_at: string;
  holding_id: number;
  ticker: string;
  asset_name: string;
  available: boolean;
  action: "继续持有" | "持有观察" | "减仓观察" | "保护利润" | "纪律止损";
  confidence: number;
  summary: string;
  thesis: string;
  evidence: string[];
  disagreement: string[];
  invalid_conditions: string[];
  risk_controls: string[];
  profit_protection_view: string;
  time_horizon: string;
  context_snapshot: Record<string, unknown>;
  empty_message: string | null;
};

export type HoldingExitSignalList = {
  generated_at: string;
  items: HoldingExitSignal[];
  count: number;
};
