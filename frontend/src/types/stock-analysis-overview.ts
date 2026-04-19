export type StockAnalysisOverviewTaskItem = {
  task_id: number;
  thread_id: number;
  thread_title: string;
  title: string;
  summary: string;
  priority: string;
  status: string;
  task_type: string;
  suggested_action?: string | null;
  reason?: string | null;
};

export type StockAnalysisOverviewActionQueueItem = {
  kind: string;
  thread_id: number;
  title: string;
  summary: string;
  priority: string;
  reason: string;
  suggested_action: string;
  target_ref?: string | null;
};

export type StockAnalysisResearchQualitySummary = {
  effective_count: number;
  mixed_count: number;
  under_evidenced_count: number;
  over_researched_count: number;
  confirmed_count: number;
  partially_confirmed_count: number;
  unclear_count: number;
  contradicted_count: number;
};

export type StockAnalysisPlanningProfileSummary = {
  balanced_count: number;
  refresh_first_count: number;
  compare_first_count: number;
  internal_first_count: number;
  external_confirm_first_count: number;
  lightweight_research_count: number;
};

export type StockAnalysisRecentFeedbackSummary = {
  total_feedback_count: number;
  effective_thread_count: number;
  high_conflict_thread_count: number;
  needs_refresh_thread_count: number;
  follow_up_required_thread_count: number;
  latest_alignment_statuses: string[];
};

export type StockAnalysisThreadOverviewItem = {
  thread_id: number;
  title: string;
  focus_type: string;
  updated_at: string;
  context_count: number;
  compare_target_count: number;
  open_task_count: number;
  high_priority_task_count: number;
  active_memory_available: boolean;
  active_compression_available: boolean;
  refresh_recommended_count: number;
  stale_context_count: number;
  latest_planning_profile?: string | null;
  latest_conflict_level?: string | null;
  latest_validation_status?: string | null;
  latest_feedback_alignment_status?: string | null;
  latest_process_quality_status?: string | null;
  thread_health_status: string;
  thread_health_score: number;
  thread_health_reason: string;
  headline_summary: string;
  next_best_action: string;
  next_best_action_reason: string;
};

export type StockAnalysisOverview = {
  generated_at: string;
  available: boolean;
  summary: string;
  thread_overview_items: StockAnalysisThreadOverviewItem[];
  high_priority_tasks: StockAnalysisOverviewTaskItem[];
  high_conflict_threads: StockAnalysisThreadOverviewItem[];
  refresh_needed_threads: StockAnalysisThreadOverviewItem[];
  research_quality_summary: StockAnalysisResearchQualitySummary;
  planning_profile_summary: StockAnalysisPlanningProfileSummary;
  recent_feedback_summary: StockAnalysisRecentFeedbackSummary;
  action_queue: StockAnalysisOverviewActionQueueItem[];
  empty_message?: string | null;
};
