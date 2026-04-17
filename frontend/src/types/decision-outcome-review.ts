export type DecisionOutcomeReview = {
  review_id: number;
  record_id: number;
  ticker: string;
  display_name: string;
  action: string;
  lifecycle_stage: string | null;
  record_date: string;
  review_date: string;
  review_horizon_days: number;
  available: boolean;
  outcome_status: string;
  outcome_score: number;
  price_change_pct: number | null;
  max_favorable_excursion_pct: number | null;
  max_adverse_excursion_pct: number | null;
  entry_reference_price: number | null;
  exit_reference_price: number | null;
  summary: string;
  what_happened: string;
  what_was_right: string;
  what_was_wrong: string;
  followup_view: string;
  risk_after_signal: string;
  context_consistency: string;
  linked_context_window_id: number | null;
  linked_event_ids_json: number[];
  empty_message: string | null;
};

export type DecisionOutcomeReviewList = {
  generated_at: string;
  items: DecisionOutcomeReview[];
  count: number;
};
