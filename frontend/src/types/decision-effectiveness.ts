export type DecisionEffectivenessBreakdownItem = {
  label: string;
  count: number;
  effective_count: number;
  partially_effective_count: number;
  failed_count: number;
  observing_count: number;
  insufficient_count: number;
  average_score: number;
};

export type DecisionEffectivenessRecentItem = {
  ticker: string;
  display_name: string;
  action: string;
  outcome_status: string;
  summary: string;
  review_date: string;
};

export type DecisionEffectivenessSummary = {
  generated_at: string;
  available: boolean;
  empty_message: string | null;
  overall_summary: string;
  overall_score: number;
  review_count: number;
  effective_count: number;
  partially_effective_count: number;
  failed_count: number;
  observing_count: number;
  insufficient_count: number;
  action_breakdown: DecisionEffectivenessBreakdownItem[];
  role_breakdown: DecisionEffectivenessBreakdownItem[];
  theme_breakdown: DecisionEffectivenessBreakdownItem[];
  recent_successes: DecisionEffectivenessRecentItem[];
  recent_failures: DecisionEffectivenessRecentItem[];
};
