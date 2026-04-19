export type StockAnalysisResearchFeedbackTaskSuggestion = {
  task_id: number;
  title: string;
  current_status: string;
  suggestion: string;
  reason: string;
};

export type StockAnalysisResearchFeedback = {
  feedback_id: number;
  thread_id: number;
  user_id: string;
  anchor_message_id: string;
  title: string;
  anchor_question_intent?: string | null;
  anchor_response_strategy?: string | null;
  anchor_mode?: string | null;
  anchor_plan_summary?: string | null;
  anchor_validation_status?: string | null;
  linked_task_ids_json: number[];
  linked_context_ids_json: number[];
  linked_memory_id?: number | null;
  linked_compression_id?: number | null;
  linked_compare_targets_json: Array<Record<string, unknown>>;
  linked_tickers_json: string[];
  linked_themes_json: string[];
  linked_outcome_review_ids_json: number[];
  linked_effectiveness_snapshot_json: Record<string, unknown>;
  linked_risk_sizing_snapshot_json: Record<string, unknown>;
  outcome_alignment_status: string;
  process_quality_status: string;
  compare_helpful: boolean;
  refresh_helpful: boolean;
  tooling_helpful: boolean;
  validation_helpful: boolean;
  what_helped_json: string[];
  what_hurt_json: string[];
  process_adjustments_json: string[];
  task_followup_suggestions_json: StockAnalysisResearchFeedbackTaskSuggestion[];
  summary: string;
  detail_note?: string | null;
  version: number;
  created_at: string;
  updated_at: string;
};

export type StockAnalysisResearchFeedbackList = {
  thread_id: number;
  items: StockAnalysisResearchFeedback[];
  latest_feedback: StockAnalysisResearchFeedback | null;
  count: number;
  generated_at: string;
};

export type StockAnalysisResearchFeedbackMutationResult = {
  thread_id: number;
  feedback: StockAnalysisResearchFeedback;
};
