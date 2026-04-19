// API Query keys constants

export const queryKeyFn =
  (defaultKey: string[]) => (queryKey: (string | number)[]) => [
    ...defaultKey,
    ...queryKey,
  ];

const STOCK_QUERY_KEYS = {
  watchlist: ["watch"],
  stockList: ["stock"],
  stockDetail: queryKeyFn(["stock", "detail"]),
  stockSearch: queryKeyFn(["stock", "search"]),
  stockPrice: queryKeyFn(["stock", "price"]),
  stockHistory: queryKeyFn(["stock", "history"]),
} as const;

const AGENT_QUERY_KEYS = {
  agentList: queryKeyFn(["agent", "list"]),
  agentInfo: queryKeyFn(["agent", "info"]),
} as const;

export const CONVERSATION_QUERY_KEYS = {
  conversationList: ["conversation"],
  conversationHistory: queryKeyFn(["conversation", "history"]),
  conversationTaskList: queryKeyFn(["conversation", "task"]),
  allConversationTaskList: ["all", "conversation", "task"],
} as const;

export const SETTING_QUERY_KEYS = {
  memoryList: ["memory"],
  modelProviders: ["model", "providers"],
  modelProviderDetail: queryKeyFn(["model", "detail"]),
} as const;

const STRATEGY_QUERY_KEYS = {
  strategyList: ["strategy", "list"],
  strategyApiKey: ["strategy", "api-key"],
  strategyTrades: queryKeyFn(["strategy", "trades"]),
  strategyHoldings: queryKeyFn(["strategy", "holdings"]),
  strategyPriceCurve: queryKeyFn(["strategy", "price-curve"]),
  strategyPrompts: ["strategy", "prompts"],
  strategyPortfolioSummary: queryKeyFn(["strategy", "portfolio-summary"]),
  strategyPerformance: queryKeyFn(["strategy", "performance"]),
} as const;

const TRADINGAGENTS_QUERY_KEYS = {
  runList: ["tradingagents", "runs"],
  runDetail: queryKeyFn(["tradingagents", "run", "detail"]),
} as const;

const PORTFOLIO_QUERY_KEYS = {
  overview: ["portfolio", "overview"],
  holdings: ["portfolio", "holdings"],
  exitSignals: ["portfolio", "exit-signals"],
  exitSignalDetail: (holdingId: number) => ["portfolio", "exit-signal", holdingId],
} as const;

const HOMEPAGE_QUERY_KEYS = {
  context: ["homepage", "context"],
} as const;

const OPPORTUNITY_POOL_QUERY_KEYS = {
  candidates: ["opportunity-pool", "candidates"],
} as const;

const ENTRY_TIMING_QUERY_KEYS = {
  signals: ["entry-timing", "signals"],
} as const;

const DECISION_ALERT_QUERY_KEYS = {
  summary: ["decision-alert", "summary"],
  list: (status: string, alertType: string, limit: number) => [
    "decision-alert",
    "list",
    status,
    alertType,
    limit,
  ],
} as const;

const STRATEGY_PREFERENCE_QUERY_KEYS = {
  templates: ["strategy-preference", "templates"],
  profile: ["strategy-preference", "profile"],
} as const;

const ASHARE_DECISION_CONTEXT_QUERY_KEYS = {
  context: (ticker: string) => ["ashare-decision-context", ticker],
} as const;

const ASHARE_DECISION_JUDGE_QUERY_KEYS = {
  result: (ticker: string) => ["ashare-decision-judge", ticker],
} as const;

const ASHARE_DAILY_WORKBENCH_QUERY_KEYS = {
  overview: ["ashare-daily-workbench", "overview"],
} as const;

const ASHARE_DAILY_SNAPSHOT_QUERY_KEYS = {
  list: (limit: number, includeToday: boolean) => [
    "ashare-daily-snapshot",
    "list",
    limit,
    includeToday,
  ],
  detail: (snapshotDate: string) => ["ashare-daily-snapshot", "detail", snapshotDate],
} as const;

const THEME_RADAR_QUERY_KEYS = {
  overview: ["theme-radar", "overview"],
} as const;

const WATCHLIST_CENTER_QUERY_KEYS = {
  overview: ["watchlist-center", "overview"],
} as const;

const HOLDING_LIFECYCLE_QUERY_KEYS = {
  overview: ["holding-lifecycle", "overview"],
  detail: (holdingId: number) => ["holding-lifecycle", "detail", holdingId],
} as const;

const EXIT_RISK_CENTER_QUERY_KEYS = {
  overview: ["exit-risk-center", "overview"],
} as const;

const DECISION_RECORD_QUERY_KEYS = {
  base: ["decision-records"],
  list: (limit: number, action: string) => ["decision-records", "list", limit, action],
  detail: (recordId: number) => ["decision-records", "detail", recordId],
} as const;

const SHORT_CYCLE_CONTEXT_EVENT_QUERY_KEYS = {
  base: ["short-cycle-context-events"],
  list: (ticker: string, limit: number) => [
    "short-cycle-context-events",
    "list",
    ticker,
    limit,
  ],
} as const;

const DECISION_CONTEXT_WINDOW_QUERY_KEYS = {
  base: ["decision-context-windows"],
  list: (ticker: string, windowSize: number, limit: number) => [
    "decision-context-windows",
    "list",
    ticker,
    windowSize,
    limit,
  ],
} as const;

const DECISION_OUTCOME_REVIEW_QUERY_KEYS = {
  base: ["decision-outcome-reviews"],
  list: (paramsKey: string) => ["decision-outcome-reviews", "list", paramsKey],
} as const;

const DECISION_EFFECTIVENESS_QUERY_KEYS = {
  summary: ["decision-effectiveness", "summary"],
} as const;

const RISK_SIZING_QUERY_KEYS = {
  summary: ["risk-sizing", "summary"],
  ticker: (ticker: string) => ["risk-sizing", "ticker", ticker],
} as const;

const STOCK_ANALYSIS_QUERY_KEYS = {
  threads: ["stock-analysis", "threads"],
  overviewBase: ["stock-analysis", "overview"],
  overview: (threadId: number) => ["stock-analysis", "overview", threadId],
  globalOverview: ["stock-analysis", "global-overview"],
  contexts: (threadId: number) => ["stock-analysis", "contexts", threadId],
  messages: (threadId: number) => ["stock-analysis", "messages", threadId],
  compareTargets: (threadId: number) => ["stock-analysis", "compare-targets", threadId],
  memories: (threadId: number) => ["stock-analysis", "memories", threadId],
  memoryDetail: (threadId: number, memoryId: number) => [
    "stock-analysis",
    "memory-detail",
    threadId,
    memoryId,
  ],
  compressions: (threadId: number) => ["stock-analysis", "compressions", threadId],
  compressionDetail: (threadId: number, compressionId: number) => [
    "stock-analysis",
    "compression-detail",
    threadId,
    compressionId,
  ],
  researchTasks: (threadId: number) => ["stock-analysis", "research-tasks", threadId],
  researchTaskDetail: (threadId: number, taskId: number) => [
    "stock-analysis",
    "research-task-detail",
    threadId,
    taskId,
  ],
  researchFeedback: (threadId: number) => [
    "stock-analysis",
    "research-feedback",
    threadId,
  ],
  researchFeedbackDetail: (threadId: number, feedbackId: number) => [
    "stock-analysis",
    "research-feedback-detail",
    threadId,
    feedbackId,
  ],
} as const;

const SYSTEM_QUERY_KEYS = {
  strategyList: queryKeyFn(["system", "strategy", "list"]),
  strategyDetail: queryKeyFn(["system", "strategy", "detail"]),
} as const;

export const API_QUERY_KEYS = {
  STOCK: STOCK_QUERY_KEYS,
  AGENT: AGENT_QUERY_KEYS,
  CONVERSATION: CONVERSATION_QUERY_KEYS,
  SETTING: SETTING_QUERY_KEYS,
  STRATEGY: STRATEGY_QUERY_KEYS,
  TRADINGAGENTS: TRADINGAGENTS_QUERY_KEYS,
  PORTFOLIO: PORTFOLIO_QUERY_KEYS,
  HOMEPAGE: HOMEPAGE_QUERY_KEYS,
  OPPORTUNITY_POOL: OPPORTUNITY_POOL_QUERY_KEYS,
  ENTRY_TIMING: ENTRY_TIMING_QUERY_KEYS,
  DECISION_ALERT: DECISION_ALERT_QUERY_KEYS,
  STRATEGY_PREFERENCE: STRATEGY_PREFERENCE_QUERY_KEYS,
  ASHARE_DECISION_CONTEXT: ASHARE_DECISION_CONTEXT_QUERY_KEYS,
  ASHARE_DECISION_JUDGE: ASHARE_DECISION_JUDGE_QUERY_KEYS,
  ASHARE_DAILY_WORKBENCH: ASHARE_DAILY_WORKBENCH_QUERY_KEYS,
  ASHARE_DAILY_SNAPSHOT: ASHARE_DAILY_SNAPSHOT_QUERY_KEYS,
  THEME_RADAR: THEME_RADAR_QUERY_KEYS,
  WATCHLIST_CENTER: WATCHLIST_CENTER_QUERY_KEYS,
  HOLDING_LIFECYCLE: HOLDING_LIFECYCLE_QUERY_KEYS,
  EXIT_RISK_CENTER: EXIT_RISK_CENTER_QUERY_KEYS,
  DECISION_RECORD: DECISION_RECORD_QUERY_KEYS,
  SHORT_CYCLE_CONTEXT_EVENT: SHORT_CYCLE_CONTEXT_EVENT_QUERY_KEYS,
  DECISION_CONTEXT_WINDOW: DECISION_CONTEXT_WINDOW_QUERY_KEYS,
  DECISION_OUTCOME_REVIEW: DECISION_OUTCOME_REVIEW_QUERY_KEYS,
  DECISION_EFFECTIVENESS: DECISION_EFFECTIVENESS_QUERY_KEYS,
  RISK_SIZING: RISK_SIZING_QUERY_KEYS,
  STOCK_ANALYSIS: STOCK_ANALYSIS_QUERY_KEYS,
  SYSTEM: SYSTEM_QUERY_KEYS,
} as const;

/**
 * Temporary language setting
 * @description This is a temporary language setting for the API.
 */
export const USER_LANGUAGE = "en-US";

export const VALUECELL_BACKEND_URL = "https://backend.valuecell.ai/api/v1";
