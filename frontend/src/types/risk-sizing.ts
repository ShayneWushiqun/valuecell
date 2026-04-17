export type RiskSizingTicker = {
  ticker: string;
  display_name: string;
  available: boolean;
  risk_level: string;
  suggested_position_range: string;
  suggested_first_entry_range: string;
  suggested_add_range: string;
  stop_loss_style: string;
  profit_protection_style: string;
  liquidity_warning: string | null;
  summary: string;
  reasons: string[];
  empty_message: string | null;
};

export type RiskSizingSummary = {
  generated_at: string;
  available: boolean;
  empty_message: string | null;
  market_risk_level: string;
  suggested_total_exposure_range: string;
  suggested_new_position_range: string;
  suggested_add_position_range: string;
  holding_risk_note: string;
  entry_risk_note: string;
  portfolio_balance_note: string;
  action_queue_note: string;
  ticker_suggestions: RiskSizingTicker[];
};
