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
