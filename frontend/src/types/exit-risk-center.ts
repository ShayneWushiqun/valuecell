export type ExitRiskItem = {
  holding_id: number;
  ticker: string;
  display_name: string;
  action: string;
  confidence: number;
  risk_type: string;
  summary: string;
  thesis: string;
  evidence: string[];
  disagreement: string[];
  invalid_conditions: string[];
  risk_controls: string[];
  liquidity_warning: string | null;
  expected_exit_plan: string;
  has_active_alerts: boolean;
  theme_name: string | null;
  role_label: string | null;
};

export type ExitRiskCenterOverview = {
  generated_at: string;
  available: boolean;
  empty_message: string | null;
  high_priority_items: ExitRiskItem[];
  profit_protection_items: ExitRiskItem[];
  discipline_stop_items: ExitRiskItem[];
  watch_items: ExitRiskItem[];
  risk_buckets: Record<string, number>;
  count: number;
};

export type ExitRiskCenterRefresh = ExitRiskCenterOverview & {
  refreshed_count: number;
};
