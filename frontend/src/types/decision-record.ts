export type DecisionRecord = {
  record_id: number;
  generated_at: string;
  record_date: string;
  ticker: string;
  display_name: string;
  holding_id: number;
  lifecycle_stage: string;
  action: string;
  confidence: number;
  summary: string;
  thesis: string;
  evidence: string[];
  disagreement: string[];
  invalid_conditions: string[];
  risk_controls: string[];
  theme_name: string | null;
  role_label: string | null;
  tradeability_state: string | null;
  expectation_state: string | null;
  source: string;
  context_window_id: number | null;
  linked_event_ids_json: number[];
  context_snapshot_json: Record<string, unknown>;
  outcome_status: string;
  review_note: string | null;
};

export type DecisionRecordList = {
  generated_at: string;
  items: DecisionRecord[];
  count: number;
};

export type DecisionRecordCapture = DecisionRecordList & {
  record_date: string;
};
