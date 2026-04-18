export type StockAnalysisMessage = {
  item_id: string;
  role: string;
  event?: string | null;
  conversation_id?: string | null;
  content: string;
  answer_basis: string;
  mode: string;
  used_context_ids: number[];
  missing_context_hints: string[];
  compared_tickers: string[];
  comparison_mode: boolean;
  stale_context_ids: number[];
  refresh_recommended_context_ids: number[];
  tool_reason?: string | null;
  tool_calls_summary: string[];
  temporary_evidence_blocks: {
    evidence_id?: string;
    type: string;
    title: string;
    summary: string;
    temporary: boolean;
    source_module?: string;
    source_label?: string;
    is_external?: boolean;
    generated_at?: string | null;
    data_time?: string | null;
    staleness_hint?: string | null;
    ticker_refs_json?: string[];
    theme_refs_json?: string[];
    payload?: Record<string, unknown>;
  }[];
  unavailable_tools: {
    tool: string;
    reason: string;
    ticker?: string;
  }[];
  used_internal_sources: string[];
  used_external_sources: string[];
  evidence_generated_at?: string | null;
  evidence_staleness_hint?: string | null;
};

export type StockAnalysisMessageList = {
  conversation_id: string;
  thread_id: number;
  items: StockAnalysisMessage[];
  count: number;
};

export type StockAnalysisMessageCreateResult = {
  conversation_id: string;
  thread_id: number;
  answer_basis: string;
  mode: string;
  used_context_ids: number[];
  missing_context_hints: string[];
  compared_tickers: string[];
  comparison_mode: boolean;
  stale_context_ids: number[];
  refresh_recommended_context_ids: number[];
  tool_reason?: string | null;
  tool_calls_summary: string[];
  temporary_evidence_blocks: {
    evidence_id?: string;
    type: string;
    title: string;
    summary: string;
    temporary: boolean;
    source_module?: string;
    source_label?: string;
    is_external?: boolean;
    generated_at?: string | null;
    data_time?: string | null;
    staleness_hint?: string | null;
    ticker_refs_json?: string[];
    theme_refs_json?: string[];
    payload?: Record<string, unknown>;
  }[];
  unavailable_tools: {
    tool: string;
    reason: string;
    ticker?: string;
  }[];
  used_internal_sources: string[];
  used_external_sources: string[];
  evidence_generated_at?: string | null;
  evidence_staleness_hint?: string | null;
  user_message: StockAnalysisMessage;
  assistant_message: StockAnalysisMessage;
};

export type StockAnalysisEvidenceSaveResult = {
  thread_id: number;
  message_id: string;
  evidence_index: number;
  context_card: import("./analysis-context-card").AnalysisContextCard;
};
