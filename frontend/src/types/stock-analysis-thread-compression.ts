export type StockAnalysisThreadCompression = {
  compression_id: number;
  thread_id: number;
  user_id: string;
  conversation_id: string;
  title: string;
  summary: string;
  current_focus: string;
  covered_until_message_id?: string | null;
  covered_message_count: number;
  source_message_ids_json: string[];
  resolved_topics_json: string[];
  open_questions_json: string[];
  recent_compare_notes_json: string[];
  recent_refresh_notes_json: string[];
  recent_tooling_notes_json: string[];
  recent_evidence_notes_json: string[];
  active_memory_id?: number | null;
  focus_tickers_json: string[];
  focus_themes_json: string[];
  compared_tickers_json: string[];
  next_questions_json: string[];
  compression_reason: string;
  is_active: boolean;
  version: number;
  source_message_count: number;
  covered_message_range_text?: string | null;
  created_at: string;
  updated_at: string;
};

export type StockAnalysisThreadCompressionList = {
  thread_id: number;
  active_compression: StockAnalysisThreadCompression | null;
  items: StockAnalysisThreadCompression[];
  count: number;
  compression_recommended: boolean;
  compression_reason?: string | null;
  uncompressed_message_count: number;
  estimated_history_size: number;
  active_compression_stale: boolean;
  generated_at: string;
};

export type StockAnalysisThreadCompressionCaptureResult = {
  compression: StockAnalysisThreadCompression;
};

export type StockAnalysisThreadCompressionActivateResult = {
  thread_id: number;
  compression: StockAnalysisThreadCompression;
};
