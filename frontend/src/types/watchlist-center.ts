export type WatchlistCenterSummary = {
  total_count: number;
  focus_count: number;
  normal_count: number;
  theme_resonance_count: number;
  opportunity_linked_count: number;
  active_alert_count: number;
  holding_linked_count: number;
};

export type WatchlistCenterItem = {
  ticker: string;
  display_name: string;
  watchlist_name: string;
  theme_name: string | null;
  status: string;
  reason: string;
  tradeability_state: string;
  expectation_gap_level: string;
  role_label: string;
  trend_quality: string;
  latest_price: string | null;
  change_percent: number | null;
  has_theme_resonance: boolean;
  has_opportunity_link: boolean;
  has_active_alert: boolean;
  has_holding: boolean;
  holding_action: string | null;
  linked_candidate_state: string | null;
  linked_judge_action: string | null;
  observation_priority: string;
  quick_note: string;
};

export type WatchlistCenterOverview = {
  generated_at: string;
  available: boolean;
  empty_message: string | null;
  summary: WatchlistCenterSummary;
  items: WatchlistCenterItem[];
  grouped: {
    focus_items: WatchlistCenterItem[];
    resonance_items: WatchlistCenterItem[];
    normal_items: WatchlistCenterItem[];
    holding_linked_items: WatchlistCenterItem[];
  };
};
