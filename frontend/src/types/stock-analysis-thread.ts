export type StockAnalysisCompareTarget = {
  target_type: "ticker" | "theme";
  ref: string;
  label: string;
  source_module: string;
  source_ref: string;
  role: "primary" | "secondary";
  order: number;
};

export type StockAnalysisThread = {
  thread_id: number;
  user_id: string;
  title: string;
  focus_type: string;
  ticker_refs_json: string[];
  theme_refs_json: string[];
  compare_targets_json: StockAnalysisCompareTarget[];
  conversation_id: string;
  context_count: number;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
};

export type StockAnalysisThreadList = {
  generated_at: string;
  items: StockAnalysisThread[];
  count: number;
};

export type StockAnalysisWorkspaceOverview = {
  generated_at: string;
  threads: StockAnalysisThread[];
  current_thread: StockAnalysisThread | null;
  context_count: number;
  available: boolean;
  empty_message: string | null;
};

export type StockAnalysisCompareTargetList = {
  thread_id: number;
  focus_type: string;
  compare_targets: StockAnalysisCompareTarget[];
  compared_tickers: string[];
  compared_themes: string[];
  comparison_mode: boolean;
};

export type StockAnalysisThreadForkResult = {
  thread: StockAnalysisThread;
  contexts: import("./analysis-context-card").AnalysisContextCard[];
  context_count: number;
};
