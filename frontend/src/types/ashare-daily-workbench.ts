export type AShareDailyWorkbenchOverview = {
  generated_at: string;
  available: boolean;
  empty_message: string | null;
  market_digest: {
    market_state: string | null;
    emotion_stage: string | null;
    temperature_score: number | null;
    action_rhythm: string | null;
    summary: string | null;
  };
  attention_digest: {
    unread_alert_count: number;
    risk_alert_count: number;
    near_entry_count: number;
    holding_risk_count: number;
    holding_profit_protection_count: number;
  };
  top_alerts: Array<{
    id: number | null;
    ticker: string;
    display_name: string;
    alert_type: string;
    priority: string;
    title: string;
    body: string;
    next_action: string;
  }>;
  top_opportunities: Array<{
    ticker: string;
    display_name: string;
    topic_name: string | null;
    action: string | null;
    candidate_state: string;
    tradeability_state: string;
    priority_score: number;
  }>;
  top_holdings_to_handle: Array<{
    holding_id: number;
    ticker: string;
    asset_name: string;
    action: string;
    confidence: number;
    summary: string;
    profit_protection_view: string;
  }>;
  top_holdings_stable: Array<{
    holding_id: number;
    ticker: string;
    asset_name: string;
    action: string;
    confidence: number;
    summary: string;
    profit_protection_view: string;
  }>;
  today_action_queue: Array<{
    title: string;
    reason: string;
    target_path: string;
  }>;
  quick_links: {
    opportunities: string;
    alerts: string;
    strategy_preferences: string;
    portfolio: string;
  };
};

export type AShareDailyWorkbenchRefreshResult = {
  generated_at: string;
  success: boolean;
  message: string;
  refreshed_alert_count: number;
  refreshed_holding_signal_count: number;
  opportunity_candidate_count: number;
  near_entry_count: number;
  holding_action_count: number;
};
