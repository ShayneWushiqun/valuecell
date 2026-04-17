export type DecisionContextEventSummary = {
  event_id: number | null;
  event_type: string;
  layer: string;
  source: string;
  direction: string;
  importance_score: number | null;
  summary: string;
  tradeability_hint: string | null;
};

export type DecisionContextWindow = {
  window_id: number;
  user_id: string;
  ticker: string;
  display_name: string;
  topic_name: string | null;
  window_start: string;
  window_end: string;
  window_size: number;
  market_state: string | null;
  position_state: string | null;
  expectation_state: string | null;
  tradeability_state: string | null;
  role_label: string | null;
  trend_quality: string | null;
  exit_liquidity_plan: string | null;
  support_events_json: DecisionContextEventSummary[];
  opposing_events_json: DecisionContextEventSummary[];
  risk_events_json: DecisionContextEventSummary[];
  summary: string;
  judgement_snapshot_json: Record<string, unknown>;
  available: boolean;
  linked_tags_json: string[];
  risk_level: string;
  disagreement_level: string;
  support_count: number;
  opposing_count: number;
  risk_count: number;
  has_holding: boolean;
  has_watchlist: boolean;
  has_opportunity: boolean;
};

export type DecisionContextWindowList = {
  generated_at: string;
  items: DecisionContextWindow[];
  count: number;
};
