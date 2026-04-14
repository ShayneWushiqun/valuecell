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
  SYSTEM: SYSTEM_QUERY_KEYS,
} as const;

/**
 * Temporary language setting
 * @description This is a temporary language setting for the API.
 */
export const USER_LANGUAGE = "en-US";

export const VALUECELL_BACKEND_URL = "https://backend.valuecell.ai/api/v1";
