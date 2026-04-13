export type DecisionAlertItem = {
  id: number | null;
  ticker: string;
  display_name: string;
  topic_name: string | null;
  alert_type: string;
  priority: string;
  title: string;
  body: string;
  next_action: string;
  action: string;
  confidence: number;
  source: string;
  reasons: string[];
  dedupe_key?: string | null;
  read_at?: string | null;
  dismissed_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type DecisionAlertSummary = {
  generated_at: string;
  available: boolean;
  items: DecisionAlertItem[];
  count: number;
  empty_message: string | null;
};

export type DecisionAlertList = {
  generated_at: string;
  unread_count: number;
  items: DecisionAlertItem[];
  count: number;
};

export type DecisionAlertReadAllResult = {
  generated_at: string;
  updated_count: number;
};
