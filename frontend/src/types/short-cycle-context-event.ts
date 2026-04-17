export type ShortCycleContextEvent = {
  event_id: number;
  user_id: string;
  ticker: string;
  display_name: string;
  topic_name: string | null;
  layer: string;
  event_type: string;
  source: string;
  occurred_at: string;
  ingested_at: string;
  importance_score: number;
  direction: string;
  time_horizon: string;
  tradeability_hint: string | null;
  summary: string;
  payload_json: Record<string, unknown>;
  record_date: string;
  is_active: boolean;
};

export type ShortCycleContextEventList = {
  generated_at: string;
  items: ShortCycleContextEvent[];
  count: number;
};
