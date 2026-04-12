export type EntryTimingSignalItem = {
  ticker: string;
  display_name: string;
  topic_name: string | null;
  action: string;
  confidence: number;
  summary: string;
  reasons: string[];
  tradeability_state: string;
  expectation_gap_view: string;
  missing_confirmations: string[];
  invalid_conditions: string[];
  candidate_state: string;
  priority_score: number;
  time_horizon: string;
};

export type EntryTimingSignals = {
  generated_at: string;
  available: boolean;
  items: EntryTimingSignalItem[];
  count: number;
  empty_message: string | null;
};
