export type AnalysisContextCard = {
  context_id: number;
  thread_id: number;
  user_id: string;
  context_type: string;
  title: string;
  subtitle: string | null;
  ticker_refs_json: string[];
  theme_refs_json: string[];
  summary: string;
  snapshot_payload_json: Record<string, unknown>;
  source_module: string;
  source_ref: string | null;
  staleness_hint: string | null;
  generated_at?: string | null;
  data_time?: string | null;
  freshness_label?: string | null;
  refresh_recommended: boolean;
  is_stale: boolean;
  refresh_supported: boolean;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
};

export type StockAnalysisRefreshChangedContext = {
  context_id: number;
  title: string;
  changed_fields: string[];
  after_freshness_label?: string | null;
};

export type StockAnalysisRefreshItem = {
  context_id: number;
  title: string;
  source_module: string;
  refresh_supported: boolean;
  status: "refreshed" | "skipped" | "failed";
  reason: string;
  before_freshness_label?: string | null;
  after_freshness_label?: string | null;
  changed_fields: string[];
  new_generated_at?: string | null;
  new_data_time?: string | null;
};

export type StockAnalysisRefreshRunResult = {
  thread_id: number;
  refreshed_count: number;
  skipped_count: number;
  failed_count: number;
  items: StockAnalysisRefreshItem[];
  summary: string;
  generated_at: string;
  refreshed_context_ids: number[];
  skipped_context_ids: number[];
  failed_context_ids: number[];
  changed_contexts: StockAnalysisRefreshChangedContext[];
};

export type AnalysisContextCardList = {
  generated_at: string;
  items: AnalysisContextCard[];
  count: number;
};

export type StockAnalysisContextImportResult = {
  thread: import("./stock-analysis-thread").StockAnalysisThread;
  context_card: AnalysisContextCard;
  contexts: AnalysisContextCard[];
};
