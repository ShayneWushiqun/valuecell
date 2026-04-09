export type HoldingAction = "持有" | "减仓" | "卖出" | "观察";
export type HoldingRiskLevel = "低" | "中" | "高";
export type HoldingConfidence = "低" | "中" | "高";

export type HoldingDiagnosis = {
  id: number;
  holding_id: number;
  diagnosis_date: string;
  action: HoldingAction;
  risk_level: HoldingRiskLevel;
  confidence: HoldingConfidence;
  summary: string;
  key_risk: string | null;
  reasons: string[];
  trigger_conditions: string[];
  invalid_conditions: string[];
  is_focus: boolean;
  raw_context: {
    current_price?: number | null;
    latest_change_percent?: number | null;
    profit_percent?: number | null;
    ma5?: number | null;
    ma10?: number | null;
    history_points?: number | null;
    news_count?: number | null;
    news_risk_title?: string | null;
    data_status?: string | null;
  };
  created_at: string;
};

export type HoldingMarketSnapshot = {
  current_price: number | null;
  latest_change_percent: number | null;
  profit_percent: number | null;
};

export type UserHolding = {
  id: number;
  user_id: string;
  ticker: string;
  exchange: string;
  asset_name: string | null;
  quantity: number;
  cost_price: number;
  position_weight: number | null;
  buy_date: string | null;
  thesis_note: string | null;
  notes: string | null;
  latest_diagnosis: HoldingDiagnosis | null;
  market_snapshot: HoldingMarketSnapshot;
  created_at: string;
  updated_at: string;
};

export type HoldingList = {
  items: UserHolding[];
  count: number;
};

export type CreateHoldingRequest = {
  ticker: string;
  asset_name?: string | null;
  quantity: number;
  cost_price: number;
  position_weight?: number | null;
  buy_date?: string | null;
  thesis_note?: string | null;
  notes?: string | null;
};

export type DailyBriefingFocusItem = {
  type: string;
  ticker: string;
  title: string;
  summary: string;
};

export type DailyBriefingMetric = {
  label: string;
  value: string;
};

export type WatchlistHighlight = {
  ticker: string;
  display_name: string | null;
  change_percent: number;
  signal: string;
};

export type DailyBriefingSummary = {
  headline: string;
  focus_items: DailyBriefingFocusItem[];
  holding_actions: DailyBriefingMetric[];
  watchlist_highlights: WatchlistHighlight[];
};

export type DailyBriefing = {
  id: number;
  user_id: string;
  briefing_date: string;
  content_markdown: string;
  summary: DailyBriefingSummary;
  created_at: string;
  updated_at: string;
};

export type PortfolioOverview = {
  briefing: DailyBriefing;
  holdings: UserHolding[];
  holding_count: number;
};
