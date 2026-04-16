export type ThemeRadarSummary = {
  active_theme_count: number;
  strengthen_count: number;
  split_count: number;
  fading_count: number;
  preferred_theme_hit_count: number;
  watchlist_resonance_count: number;
  opportunity_resonance_count: number;
};

export type ThemeRadarItem = {
  theme_code: string;
  theme_name: string;
  theme_state: string;
  rank: number;
  score: number;
  hot_level: number;
  preferred_market: string;
  participation_hint: string;
  etf_hint: {
    title: string;
    summary: string;
    risk_hint: string;
  } | null;
  primary_representative: string | null;
  representative_tickers: string[];
  core_leaders_json: string[];
  metrics: Record<string, number | string | null>;
  watchlist_resonance_count: number;
  opportunity_resonance_count: number;
  has_preference_match: boolean;
  risk_tags: string[];
  observation_summary: string;
};

export type ThemeRadarOverview = {
  generated_at: string;
  available: boolean;
  empty_message: string | null;
  summary: ThemeRadarSummary;
  items: ThemeRadarItem[];
  grouped: {
    strengthen_items: ThemeRadarItem[];
    active_items: ThemeRadarItem[];
    split_items: ThemeRadarItem[];
    fading_items: ThemeRadarItem[];
  };
};
