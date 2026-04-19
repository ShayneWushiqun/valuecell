export type StockAnalysisResearchTask = {
  task_id: number;
  thread_id: number;
  user_id: string;
  title: string;
  summary: string;
  task_type:
    | "compare_followup"
    | "refresh_needed"
    | "tooling_check"
    | "memory_recheck"
    | "compression_recheck"
    | "risk_recheck"
    | "next_question"
    | "thesis_validation";
  status: "open" | "completed" | "dismissed";
  priority: "high" | "medium" | "low";
  source_kind:
    | "manual"
    | "memory"
    | "compression"
    | "compare"
    | "refresh"
    | "tooling"
    | "assistant_suggestion"
    | string;
  source_ref?: string | null;
  related_tickers_json: string[];
  related_themes_json: string[];
  related_context_ids_json: number[];
  related_memory_id?: number | null;
  related_compression_id?: number | null;
  related_message_id?: string | null;
  resolution_note?: string | null;
  dismiss_reason?: string | null;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  dismissed_at?: string | null;
  is_focus_related?: boolean;
  is_related_to_latest_message?: boolean;
  is_planning_influencer?: boolean;
  is_primary_research_anchor?: boolean;
  suggested_planning_action?: string;
};

export type StockAnalysisResearchTaskList = {
  thread_id: number;
  items: StockAnalysisResearchTask[];
  count: number;
  open_count: number;
  high_priority_open_count: number;
  last_generated_at?: string | null;
  has_actionable_gap: boolean;
  actionable_gap_summary?: string | null;
  generated_at: string;
};

export type StockAnalysisResearchTaskMutationResult = {
  thread_id: number;
  task: StockAnalysisResearchTask;
};

export type StockAnalysisResearchTaskGenerateResult = {
  thread_id: number;
  created_count: number;
  updated_count: number;
  items: StockAnalysisResearchTask[];
  last_generated_at?: string | null;
  summary?: string | null;
};
