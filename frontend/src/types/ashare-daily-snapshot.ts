export type AShareDailySnapshotListItem = {
  snapshot_date: string;
  generated_at: string | null;
  market_digest: {
    market_state?: string | null;
    emotion_stage?: string | null;
    temperature_score?: number | null;
    action_rhythm?: string | null;
    summary?: string | null;
  };
  attention_digest: {
    unread_alert_count?: number;
    risk_alert_count?: number;
    near_entry_count?: number;
    holding_risk_count?: number;
    holding_profit_protection_count?: number;
  };
  brief_action_queue: string[];
  top_opportunity_count: number;
  top_holding_action_count: number;
};

export type AShareDailySnapshotList = {
  generated_at: string;
  count: number;
  items: AShareDailySnapshotListItem[];
};

export type AShareDailySnapshotDetail = {
  snapshot_date: string;
  generated_at: string | null;
  market_digest: {
    market_state?: string | null;
    emotion_stage?: string | null;
    temperature_score?: number | null;
    action_rhythm?: string | null;
    summary?: string | null;
  };
  attention_digest: {
    unread_alert_count?: number;
    risk_alert_count?: number;
    near_entry_count?: number;
    holding_risk_count?: number;
    holding_profit_protection_count?: number;
  };
  top_alerts: Array<Record<string, unknown>>;
  top_opportunities: Array<Record<string, unknown>>;
  top_holdings_to_handle: Array<Record<string, unknown>>;
  top_holdings_stable: Array<Record<string, unknown>>;
  today_action_queue: Array<{
    title?: string;
    reason?: string;
    target_path?: string;
  }>;
  metadata: Record<string, unknown>;
};

export type AShareDailySnapshotRefreshResult = {
  generated_at: string;
  snapshot_date: string;
  created_or_updated: "created" | "updated";
  summary: string;
  snapshot: AShareDailySnapshotDetail;
};
