export type StockAnalysisThreadMemory = {
  memory_id: number;
  thread_id: number;
  user_id: string;
  title: string;
  summary: string;
  stance: string;
  confidence: number;
  time_horizon: string;
  focus_tickers_json: string[];
  focus_themes_json: string[];
  compared_tickers_json: string[];
  support_points_json: string[];
  opposing_points_json: string[];
  risk_points_json: string[];
  key_uncertainties_json: string[];
  invalidation_conditions_json: string[];
  next_questions_json: string[];
  next_data_to_check_json: string[];
  linked_context_ids_json: number[];
  linked_message_ids_json: string[];
  linked_compare_targets_json: Array<Record<string, unknown>>;
  source_snapshot_json: Record<string, unknown>;
  is_active: boolean;
  version: number;
  linked_context_count: number;
  linked_message_count: number;
  compare_target_count: number;
  created_at: string;
  updated_at: string;
};

export type StockAnalysisThreadMemoryList = {
  thread_id: number;
  active_memory: StockAnalysisThreadMemory | null;
  items: StockAnalysisThreadMemory[];
  count: number;
  generated_at: string;
};

export type StockAnalysisThreadMemoryCaptureResult = {
  memory: StockAnalysisThreadMemory;
};

export type StockAnalysisThreadMemoryActivateResult = {
  thread_id: number;
  memory: StockAnalysisThreadMemory;
};
