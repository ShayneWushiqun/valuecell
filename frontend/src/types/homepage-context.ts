export type HomepageSignal = {
  label: string;
  value: string | number | null;
};

export type HomepageIndexQuote = {
  label: string;
  ticker: string;
  price: string | null;
  change_percent: number | null;
};

export type HomepageStagePoint = {
  trading_date: string;
  cycle_stage: string;
  stage_score: number;
  up_limit_count: number | null;
  down_limit_count: number | null;
  broken_limit_count: number | null;
  highest_board: number | null;
  action_hint: string | null;
};

export type HomepageTurningPoint = {
  trading_date: string;
  from_stage: string;
  to_stage: string;
};

export type HomepageMarketOverview = {
  available: boolean;
  market_state: string | null;
  summary: string | null;
  confidence: string | null;
  action_hint: string | null;
  signals: HomepageSignal[];
  breadth_items: HomepageSignal[];
  index_quotes: HomepageIndexQuote[];
  score: number | null;
  empty_message: string | null;
};

export type HomepageEmotionCycle = {
  available: boolean;
  cycle_stage: string | null;
  summary: string | null;
  action_hint: string | null;
  trend_direction: string | null;
  stage_points: HomepageStagePoint[];
  turning_points: HomepageTurningPoint[];
  default_window_days: number;
  empty_message: string | null;
};

export type HomepageThemeInstitution = {
  source: string;
  net_inflow: number;
};

export type HomepageThemeMetrics = {
  score: number;
  change_value: number;
  ths_flow_value: number;
  dc_flow_value: number;
  kpl_count: number;
  hot_count: number;
};

export type HomepageThemeItem = {
  trading_date: string | null;
  theme_name: string;
  theme_code: string;
  theme_state: string;
  summary: string;
  representative_tickers_json: string[];
  rank: number;
  expectation_gap_level: string;
  core_leaders_json: string[];
  primary_representative: string | null;
  trend_state: string;
  hot_level: number;
  is_suitable_for_direct_participation: boolean;
  participation_hint: string;
  preferred_market: string;
  core_institutions_json: HomepageThemeInstitution[];
  etf_hint: {
    title: string;
    summary: string;
    risk_hint: string;
  } | null;
  metrics: HomepageThemeMetrics;
};

export type HomepageThemeFocus = {
  available: boolean;
  items: HomepageThemeItem[];
  empty_message: string | null;
};

export type HomepageActionFramework = {
  available: boolean;
  title: string;
  summary: string | null;
  focus_points: string[];
  avoid_points: string[];
  participation_preferences: string[];
  etf_strategy_hint: string | null;
  empty_message: string | null;
};

export type HomepageWatchlistObservationItem = {
  ticker: string;
  display_name: string;
  watchlist_name: string;
  price: string | null;
  change_percent: number | null;
  status: string;
  reason: string;
  theme_name: string | null;
  tradeability_state: string;
  expectation_gap_level: string;
  role_label: string;
  trend_quality: string;
};

export type HomepageWatchlistObservation = {
  available: boolean;
  items: HomepageWatchlistObservationItem[];
  empty_message: string | null;
};

export type HomepageMetric = {
  label: string;
  value: string;
};

export type HomepagePortfolioHandling = {
  available: boolean;
  summary: string | null;
  holding_count: number;
  focus_count: number;
  action_breakdown: HomepageMetric[];
  empty_message: string | null;
};

export type HomepageRiskControl = {
  available: boolean;
  summary: string;
  position_suggestion: string;
  total_position_range: string;
  single_position_range: string;
  build_strategy: string;
  theme_concentration_hint: string;
  signals: string[];
  empty_message: string | null;
};

export type HomepageContext = {
  generated_at: string;
  market_overview: HomepageMarketOverview;
  emotion_cycle: HomepageEmotionCycle;
  theme_focus: HomepageThemeFocus;
  action_framework: HomepageActionFramework;
  watchlist_observation: HomepageWatchlistObservation;
  portfolio_handling: HomepagePortfolioHandling;
  risk_control: HomepageRiskControl;
};
