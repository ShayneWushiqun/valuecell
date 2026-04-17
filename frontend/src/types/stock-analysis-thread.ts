export type StockAnalysisThread = {
  thread_id: number;
  user_id: string;
  title: string;
  focus_type: string;
  ticker_refs_json: string[];
  theme_refs_json: string[];
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
