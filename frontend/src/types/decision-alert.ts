export type DecisionAlertItem = {
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
};

export type DecisionAlertSummary = {
  generated_at: string;
  available: boolean;
  items: DecisionAlertItem[];
  count: number;
  empty_message: string | null;
};
