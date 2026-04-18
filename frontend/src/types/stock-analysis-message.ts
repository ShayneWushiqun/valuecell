export type StockAnalysisMessage = {
  item_id: string;
  role: string;
  event?: string | null;
  conversation_id?: string | null;
  content: string;
  answer_basis: string;
  used_context_ids: number[];
  missing_context_hints: string[];
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
  used_context_ids: number[];
  missing_context_hints: string[];
  user_message: StockAnalysisMessage;
  assistant_message: StockAnalysisMessage;
};
