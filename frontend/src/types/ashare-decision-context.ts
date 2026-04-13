export type AShareDecisionAlertItem = {
  id: number | null;
  alert_type: string;
  priority: string;
  title: string;
  body: string;
  next_action: string;
  action: string;
  confidence: number;
  reasons: string[];
  read_at: string | null;
  dismissed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type AShareDecisionContext = {
  generated_at: string;
  ticker: string;
  available: boolean;
  empty_message: string | null;
  market_context: {
    market_state: string | null;
    emotion_stage: string | null;
    temperature_score: number | null;
    action_rhythm: string | null;
    summary: string | null;
  };
  theme_context: {
    topic_name: string | null;
    source_tags: string[];
    role_label: string | null;
    trend_quality: string | null;
  };
  candidate_context: {
    priority_score: number | null;
    candidate_state: string | null;
    tradeability_state: string | null;
    expectation_gap_level: string | null;
    matched_preferences: string[];
    preference_adjustments: Array<{ label: string; delta: number }>;
    reasons: string[];
    time_horizon: string | null;
  };
  entry_timing_context: {
    action: string | null;
    confidence: number | null;
    summary: string | null;
    reasons: string[];
    missing_confirmations: string[];
    invalid_conditions: string[];
  };
  alert_context: {
    active_count: number;
    items: AShareDecisionAlertItem[];
  };
  preference_context: {
    template_id: string | null;
    template_title: string | null;
    risk_style: string | null;
    buy_style: string | null;
    preferred_themes: string[];
    avoid_risks: string[];
    accept_high_position: boolean | null;
    prefer_expectation_gap: boolean | null;
    prefer_leader_or_core: boolean | null;
    note: string | null;
  };
  portfolio_context: {
    has_position: boolean;
    summary: string | null;
    latest_action: string | null;
    risk_level: string | null;
    market_snapshot: Record<string, unknown> | null;
  };
  risk_context: {
    items: string[];
  };
  missing_context: string[];
  rule_based_judgement: {
    action: string;
    summary: string;
    reasons: string[];
    missing_confirmations: string[];
    invalid_conditions: string[];
  };
  agent_prompt_preview: string;
};
