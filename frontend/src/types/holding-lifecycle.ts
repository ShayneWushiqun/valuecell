export type HoldingLifecycleStage =
  | "建仓观察期"
  | "主升持有期"
  | "分歧确认期"
  | "退潮减仓期"
  | "破逻辑退出期";

export type HoldingLifecycleItem = {
  holding_id: number;
  ticker: string;
  display_name: string;
  lifecycle_stage: HoldingLifecycleStage;
  action: string;
  confidence: number;
  summary: string;
  theme_name: string | null;
  role_label: string | null;
  trend_quality: string | null;
  tradeability_state: string | null;
  expectation_state: string | null;
  observation_window: string;
  invalid_conditions: string[];
  risk_controls: string[];
  profit_protection_view: string | null;
  position_hint: string;
  has_active_alerts: boolean;
  decision_context_available: boolean;
};

export type HoldingLifecycleOverview = {
  generated_at: string;
  available: boolean;
  empty_message: string | null;
  items: HoldingLifecycleItem[];
  count: number;
  summary: {
    total_count: number;
    need_attention_count: number;
    major_hold_count: number;
    high_risk_count: number;
    active_alert_count: number;
  };
};

export type HoldingLifecycleDetail = {
  generated_at: string;
  available: boolean;
  empty_message: string | null;
  item: HoldingLifecycleItem;
};
