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
  tool_reason?: string | null;
  tool_calls_summary: string[];
  temporary_evidence_blocks: {
    type: string;
    title: string;
    summary: string;
    temporary: boolean;
    payload?: Record<string, unknown>;
  }[];
  unavailable_tools: {
    tool: string;
    reason: string;
    ticker?: string;
  }[];
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
  tool_reason?: string | null;
  tool_calls_summary: string[];
  temporary_evidence_blocks: {
    type: string;
    title: string;
    summary: string;
    temporary: boolean;
    payload?: Record<string, unknown>;
  }[];
  unavailable_tools: {
    tool: string;
    reason: string;
    ticker?: string;
  }[];
  user_message: StockAnalysisMessage;
  assistant_message: StockAnalysisMessage;
};
