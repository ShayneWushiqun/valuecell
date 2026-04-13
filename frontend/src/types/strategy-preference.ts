export type StrategyPreferenceTemplate = {
  template_id: string;
  title: string;
  summary: string;
  preferred_themes: string[];
  holding_period_days: number;
  risk_style: "steady" | "balanced" | "aggressive";
  buy_style: "pullback" | "breakout" | "low_absorb" | "right_side";
  avoid_risks: string[];
  accept_high_position: boolean;
  prefer_expectation_gap: boolean;
  prefer_leader_or_core: boolean;
  note: string;
};

export type StrategyPreferenceTemplateList = {
  items: StrategyPreferenceTemplate[];
  count: number;
};

export type StrategyPreferenceProfile = {
  profile_id: number | null;
  kind: string;
  schema_version: number;
  template_id: string;
  template_title: string | null;
  preferred_themes: string[];
  holding_period_days: number;
  risk_style: "steady" | "balanced" | "aggressive";
  buy_style: "pullback" | "breakout" | "low_absorb" | "right_side";
  avoid_risks: string[];
  accept_high_position: boolean;
  prefer_expectation_gap: boolean;
  prefer_leader_or_core: boolean;
  note: string;
};

export type UpdateStrategyPreferencePayload = Omit<
  StrategyPreferenceProfile,
  "profile_id" | "kind" | "schema_version" | "template_title"
>;
