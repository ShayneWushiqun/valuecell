export type OpportunityCandidateItem = {
  ticker: string;
  display_name: string;
  latest_price: string | null;
  change_percent: number | null;
  topic_name: string | null;
  candidate_state: string;
  priority_score: number;
  expectation_gap_level: string;
  expectation_gap_score: number;
  continuity_score: number;
  tradeability_state: string;
  role_label: string;
  trend_quality: string;
  ranking_bucket: string;
  reasons: string[];
  time_horizon: string;
  source_tags: string[];
  action_hint: string;
  missing_confirmations: string[];
  invalid_conditions: string[];
};

export type OpportunitySourceSummary = {
  watchlist_count: number;
  theme_candidate_count: number;
  candidate_count: number;
};

export type OpportunityPool = {
  generated_at: string;
  available: boolean;
  items: OpportunityCandidateItem[];
  count: number;
  empty_message: string | null;
  source_summary: OpportunitySourceSummary;
};
