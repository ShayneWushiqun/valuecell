import BackButton from "@valuecell/button/back-button";
import { Copy, Plus, RefreshCw, Send, Trash2, Zap } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { toast } from "sonner";
import { useGetDecisionContextWindows } from "@/api/decision-context-window";
import { useGetDecisionEffectivenessSummary } from "@/api/decision-effectiveness";
import { useGetDecisionAlertSummary } from "@/api/decision-alert";
import { useGetDecisionOutcomeReviews } from "@/api/decision-outcome-review";
import { useGetHoldingLifecycleOverview } from "@/api/holding-lifecycle";
import { useGetOpportunityCandidates } from "@/api/opportunity-pool";
import { useGetRiskSizingSummary } from "@/api/risk-sizing";
import {
  useActivateStockAnalysisThreadCompression,
  useCaptureStockAnalysisThreadCompression,
  useGetStockAnalysisThreadCompressions,
  useRefreshStockAnalysisThreadCompression,
} from "@/api/stock-analysis-thread-compression";
import {
  useActivateStockAnalysisThreadMemory,
  useCaptureStockAnalysisThreadMemory,
  useGetStockAnalysisThreadMemories,
  useRefreshStockAnalysisThreadMemory,
} from "@/api/stock-analysis-thread-memory";
import {
  useCompleteStockAnalysisResearchTask,
  useCreateStockAnalysisResearchTask,
  useDismissStockAnalysisResearchTask,
  useGenerateStockAnalysisResearchTasks,
  useGetStockAnalysisResearchTasks,
  useReopenStockAnalysisResearchTask,
} from "@/api/stock-analysis-research-task";
import {
  useCreateStockAnalysisMessage,
  useCreateStockAnalysisThread,
  useDeleteStockAnalysisContext,
  useDeleteStockAnalysisThread,
  useDuplicateStockAnalysisThread,
  useForkStockAnalysisThread,
  useGetStockAnalysisCompareTargets,
  useGetStockAnalysisContexts,
  useGetStockAnalysisMessages,
  useGetStockAnalysisWorkspaceOverview,
  useImportStockAnalysisContext,
  useRefreshStockAnalysisContext,
  useRefreshStaleStockAnalysisContexts,
  useSaveStockAnalysisEvidence,
  useUpdateStockAnalysisCompareTargets,
  useUpdateStockAnalysisContext,
  useUpdateStockAnalysisThread,
} from "@/api/stock-analysis";
import { StockAnalysisCompareTray } from "@/app/home/components/stock-analysis-compare-tray";
import { StockAnalysisCompressionPanel } from "@/app/home/components/stock-analysis-compression-panel";
import { StockAnalysisContextCard } from "@/app/home/components/stock-analysis-context-card";
import { StockAnalysisExecutionTrace } from "@/app/home/components/stock-analysis-execution-trace";
import { StockAnalysisForkDialog } from "@/app/home/components/stock-analysis-fork-dialog";
import { StockAnalysisMemoryPanel } from "@/app/home/components/stock-analysis-memory-panel";
import { StockAnalysisResearchTaskPanel } from "@/app/home/components/stock-analysis-research-task-panel";
import { StockAnalysisRefreshSummary } from "@/app/home/components/stock-analysis-refresh-summary";
import { StockAnalysisThreadSummary } from "@/app/home/components/stock-analysis-thread-summary";
import { StockAnalysisValidationSummary } from "@/app/home/components/stock-analysis-validation-summary";
import { useGetThemeRadarOverview } from "@/api/theme-radar";
import { useGetTradingAgentsRuns } from "@/api/tradingagents";
import { useGetWatchlistCenterOverview } from "@/api/watchlist-center";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import type {
  AnalysisContextCard,
  StockAnalysisRefreshRunResult,
} from "@/types/analysis-context-card";
import type {
  StockAnalysisCompareTarget,
  StockAnalysisThread,
} from "@/types/stock-analysis-thread";
import type { StockAnalysisResearchTask } from "@/types/stock-analysis-research-task";

const FOCUS_OPTIONS = [
  "ticker",
  "theme",
  "comparison",
  "holding",
  "tradingagents_followup",
  "mixed",
] as const;

const splitRefs = (value: string) =>
  value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

const formatTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN");
};

const resolveFreshnessLabel = (value?: string | null) => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  const diffMs = Date.now() - date.getTime();
  const diffDays = diffMs / (1000 * 60 * 60 * 24);
  if (diffDays < 1) return "当日补数";
  if (diffDays <= 3) return "近 3 日";
  return "可能已过时";
};

const isAssistantRole = (role: string) => {
  const normalized = role.toLowerCase();
  return normalized.includes("assistant") || normalized.includes("agent");
};

const readStringArray = (value: unknown) =>
  Array.isArray(value)
    ? value.map((item) => String(item)).filter(Boolean)
    : [];

const readTaskIds = (value: unknown) =>
  Array.isArray(value)
    ? value
        .map((item) => Number(item))
        .filter((item) => Number.isFinite(item) && item > 0)
    : [];

const buildManualCompareTarget = (
  type: "ticker" | "theme",
  ref: string,
): StockAnalysisCompareTarget => ({
  target_type: type,
  ref,
  label: ref,
  source_module: "manual",
  source_ref: ref,
  role: "secondary",
  order: 0,
});

const buildCompareTargetFromCard = (
  card: AnalysisContextCard,
): StockAnalysisCompareTarget | null => {
  if (card.source_module === "theme" && card.theme_refs_json[0]) {
    return {
      target_type: "theme",
      ref: card.theme_refs_json[0],
      label: card.theme_refs_json[0],
      source_module: card.source_module,
      source_ref: card.source_ref || card.theme_refs_json[0],
      role: "secondary",
      order: 0,
    };
  }
  if (card.ticker_refs_json[0]) {
    return {
      target_type: "ticker",
      ref: card.ticker_refs_json[0],
      label: card.ticker_refs_json[0],
      source_module: card.source_module,
      source_ref: card.source_ref || card.ticker_refs_json[0],
      role: "secondary",
      order: 0,
    };
  }
  if (card.theme_refs_json[0]) {
    return {
      target_type: "theme",
      ref: card.theme_refs_json[0],
      label: card.theme_refs_json[0],
      source_module: card.source_module,
      source_ref: card.source_ref || card.theme_refs_json[0],
      role: "secondary",
      order: 0,
    };
  }
  return null;
};

const normalizeCompareTargetsForSave = (
  targets: StockAnalysisCompareTarget[],
): StockAnalysisCompareTarget[] =>
  targets.map((target, index) => ({
    ...target,
    role: index === 0 ? "primary" : "secondary",
    order: index,
  }));

const compareTargetKey = (target: StockAnalysisCompareTarget) =>
  `${target.target_type}:${target.ref}:${target.source_module}`;

export default function StockAnalysis() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedThreadId = Number(searchParams.get("threadId") || 0) || null;
  const sourceModuleParam = searchParams.get("sourceModule");
  const sourceRefParam = searchParams.get("sourceRef");
  const createThreadParam = searchParams.get("createThread") === "1";
  const [newTitle, setNewTitle] = useState("");
  const [newFocusType, setNewFocusType] = useState<string>("mixed");
  const [newTickerRefs, setNewTickerRefs] = useState("");
  const [newThemeRefs, setNewThemeRefs] = useState("");
  const [renameOpen, setRenameOpen] = useState(false);
  const [addContextOpen, setAddContextOpen] = useState(false);
  const [addContextSource, setAddContextSource] = useState("tradingagents_run");
  const [addContextMode, setAddContextMode] = useState<"append" | "replace">(
    "append",
  );
  const [renameTitle, setRenameTitle] = useState("");
  const [messageInput, setMessageInput] = useState("");
  const [activeResearchTaskId, setActiveResearchTaskId] = useState<number | null>(null);
  const [pendingMessageAction, setPendingMessageAction] = useState<
    "send" | "tooling" | "refresh" | null
  >(null);
  const [editingThread, setEditingThread] = useState<StockAnalysisThread | null>(null);
  const [forkDialogOpen, setForkDialogOpen] = useState(false);
  const [forkTitle, setForkTitle] = useState("");
  const [forkSelectedContextIds, setForkSelectedContextIds] = useState<number[]>([]);
  const [includeCompareTargetsInFork, setIncludeCompareTargetsInFork] = useState(true);
  const [pinImportedContexts, setPinImportedContexts] = useState(false);
  const [seedFromActiveMemory, setSeedFromActiveMemory] = useState(false);
  const [forkFocusTypeOverride, setForkFocusTypeOverride] = useState("inherit");
  const [lastRefreshRun, setLastRefreshRun] =
    useState<StockAnalysisRefreshRunResult | null>(null);
  const [recentContextRefreshState, setRecentContextRefreshState] = useState<
    Record<number, { status: "refreshed" | "skipped" | "failed"; reason?: string | null }>
  >({});
  const autoImportKeyRef = useRef<string | null>(null);

  const { data: overview, isLoading, isError } =
    useGetStockAnalysisWorkspaceOverview(selectedThreadId);
  const { data: contexts, isLoading: contextsLoading } =
    useGetStockAnalysisContexts(selectedThreadId);
  const { data: messages, isLoading: messagesLoading } =
    useGetStockAnalysisMessages(selectedThreadId);
  const { data: compareTargetData } =
    useGetStockAnalysisCompareTargets(selectedThreadId);
  const { data: memoryData, isLoading: memoriesLoading } =
    useGetStockAnalysisThreadMemories(selectedThreadId);
  const { data: compressionData, isLoading: compressionsLoading } =
    useGetStockAnalysisThreadCompressions(selectedThreadId);
  const { data: researchTaskData, isLoading: researchTasksLoading } =
    useGetStockAnalysisResearchTasks(selectedThreadId);
  const { data: tradingRuns } = useGetTradingAgentsRuns();
  const { data: holdingOverview } = useGetHoldingLifecycleOverview();
  const { data: opportunityOverview } = useGetOpportunityCandidates();
  const { data: watchlistOverview } = useGetWatchlistCenterOverview();
  const { data: themeOverview } = useGetThemeRadarOverview();
  const { data: alertSummary } = useGetDecisionAlertSummary();
  const { data: decisionWindows } = useGetDecisionContextWindows({ limit: 80 });
  const { data: decisionReviews } = useGetDecisionOutcomeReviews({ limit: 60 });
  const { data: decisionEffectiveness } = useGetDecisionEffectivenessSummary();
  const { data: riskSizingSummary } = useGetRiskSizingSummary();
  const createThread = useCreateStockAnalysisThread();
  const updateThread = useUpdateStockAnalysisThread();
  const deleteThread = useDeleteStockAnalysisThread();
  const duplicateThread = useDuplicateStockAnalysisThread();
  const updateContext = useUpdateStockAnalysisContext();
  const deleteContext = useDeleteStockAnalysisContext();
  const refreshContext = useRefreshStockAnalysisContext();
  const importContext = useImportStockAnalysisContext();
  const createMessage = useCreateStockAnalysisMessage();
  const captureThreadCompression = useCaptureStockAnalysisThreadCompression();
  const activateThreadCompression = useActivateStockAnalysisThreadCompression();
  const refreshThreadCompression = useRefreshStockAnalysisThreadCompression();
  const captureThreadMemory = useCaptureStockAnalysisThreadMemory();
  const activateThreadMemory = useActivateStockAnalysisThreadMemory();
  const refreshThreadMemory = useRefreshStockAnalysisThreadMemory();
  const generateResearchTasks = useGenerateStockAnalysisResearchTasks();
  const createResearchTask = useCreateStockAnalysisResearchTask();
  const completeResearchTask = useCompleteStockAnalysisResearchTask();
  const reopenResearchTask = useReopenStockAnalysisResearchTask();
  const dismissResearchTask = useDismissStockAnalysisResearchTask();
  const saveEvidence = useSaveStockAnalysisEvidence();
  const updateCompareTargets = useUpdateStockAnalysisCompareTargets();
  const forkThread = useForkStockAnalysisThread();
  const refreshStaleContexts = useRefreshStaleStockAnalysisContexts();

  const threads = overview?.threads || [];
  const currentThread = useMemo(() => {
    if (!selectedThreadId) return overview?.current_thread || null;
    return threads.find((item) => item.thread_id === selectedThreadId) || null;
  }, [overview?.current_thread, selectedThreadId, threads]);
  const contextItems = contexts?.items || [];
  const compareTargets =
    compareTargetData?.compare_targets || currentThread?.compare_targets_json || [];
  const activeMemory = memoryData?.active_memory || null;
  const threadMemories = memoryData?.items || [];
  const activeCompression = compressionData?.active_compression || null;
  const threadCompressions = compressionData?.items || [];
  const threadResearchTasks = researchTaskData?.items || [];
  const latestAssistantMessage = useMemo(
    () =>
      [...(messages?.items || [])]
        .reverse()
        .find((item) => isAssistantRole(item.role)) || null,
    [messages?.items],
  );
  const latestRelatedTaskIds = useMemo(
    () => readTaskIds(latestAssistantMessage?.related_task_ids),
    [latestAssistantMessage?.related_task_ids],
  );
  const latestFocusTickers = useMemo(
    () => readStringArray(latestAssistantMessage?.focus_tickers),
    [latestAssistantMessage?.focus_tickers],
  );
  const latestFocusThemes = useMemo(
    () => readStringArray(latestAssistantMessage?.focus_themes),
    [latestAssistantMessage?.focus_themes],
  );
  const latestValidationSummary = useMemo(
    () =>
      latestAssistantMessage?.validation_summary &&
      Object.keys(latestAssistantMessage.validation_summary).length
        ? latestAssistantMessage.validation_summary
        : null,
    [latestAssistantMessage?.validation_summary],
  );
  const latestValidationSummaryText = useMemo(
    () =>
      latestValidationSummary && typeof latestValidationSummary.summary === "string"
        ? latestValidationSummary.summary
        : null,
    [latestValidationSummary],
  );
  const latestExecutedStepTypes = useMemo(
    () =>
      Array.isArray(latestAssistantMessage?.executed_steps)
        ? latestAssistantMessage.executed_steps
            .map((item) =>
              item && typeof item.step_type === "string" ? item.step_type : "",
            )
            .filter(Boolean)
        : [],
    [latestAssistantMessage?.executed_steps],
  );
  const contextTitleMap = useMemo(
    () => new Map(contextItems.map((item) => [item.context_id, item.title])),
    [contextItems],
  );
  const compareTargetKeySet = useMemo(
    () => new Set(compareTargets.map((target) => compareTargetKey(target))),
    [compareTargets],
  );
  const staleContextCount = contextItems.filter((item) => item.is_stale).length;
  const refreshRecommendedCount = contextItems.filter(
    (item) => item.refresh_recommended,
  ).length;
  const savedEvidenceCount = contextItems.filter(
    (item) => item.context_type === "temporary_evidence_saved",
  ).length;

  useEffect(() => {
    if (!selectedThreadId && overview?.current_thread?.thread_id) {
      setSearchParams({ threadId: String(overview.current_thread.thread_id) });
    }
  }, [overview?.current_thread?.thread_id, selectedThreadId, setSearchParams]);

  useEffect(() => {
    setForkSelectedContextIds([]);
    setForkDialogOpen(false);
    setForkTitle("");
    setSeedFromActiveMemory(false);
    setActiveResearchTaskId(null);
    setLastRefreshRun(null);
    setRecentContextRefreshState({});
  }, [selectedThreadId]);

  useEffect(() => {
    if (!sourceModuleParam || !sourceRefParam) return;
    const autoImportKey = `${sourceModuleParam}:${sourceRefParam}:${createThreadParam ? "new" : selectedThreadId || "none"}`;
    if (autoImportKeyRef.current === autoImportKey) return;
    autoImportKeyRef.current = autoImportKey;
    void (async () => {
      try {
        const response = await importContext.mutateAsync({
          source_module: sourceModuleParam,
          source_ref: sourceRefParam,
          target_thread_id: createThreadParam ? undefined : selectedThreadId || undefined,
          create_new_thread: createThreadParam || !selectedThreadId,
          mode: "append",
        });
        toast.success("已按入口参数导入上下文卡片");
        setSearchParams({ threadId: String(response.data.thread.thread_id) });
      } catch {
        toast.error("自动导入上下文失败");
      }
    })();
  }, [
    createThreadParam,
    importContext,
    selectedThreadId,
    setSearchParams,
    sourceModuleParam,
    sourceRefParam,
  ]);

  const contextSourceItems = useMemo(() => {
    if (addContextSource === "tradingagents_run") {
      return (tradingRuns?.runs || []).map((item) => ({
        ref: item.run_id,
        title: `${item.symbol} TradingAgents 分析`,
        subtitle: `${item.status} · ${item.created_at}`,
        summary: item.decision_signal || item.summary?.final_decision || "暂无运行摘要",
      }));
    }
    if (addContextSource === "holding") {
      return (holdingOverview?.items || []).map((item) => ({
        ref: String(item.holding_id),
        title: `${item.display_name} 持仓处理`,
        subtitle: `${item.lifecycle_stage} · ${item.action}`,
        summary: item.summary,
      }));
    }
    if (addContextSource === "opportunity") {
      return (opportunityOverview?.items || []).map((item) => ({
        ref: item.ticker,
        title: `${item.display_name} 机会池候选`,
        subtitle: `${item.topic_name || "未分类"} · ${item.candidate_state}`,
        summary: item.action_hint,
      }));
    }
    if (addContextSource === "watchlist") {
      return (watchlistOverview?.items || []).map((item) => ({
        ref: item.ticker,
        title: `${item.display_name} 观察池`,
        subtitle: `${item.status} · ${item.tradeability_state}`,
        summary: item.reason,
      }));
    }
    if (addContextSource === "theme") {
      return (themeOverview?.items || []).map((item) => ({
        ref: item.theme_code,
        title: `${item.theme_name} 题材雷达`,
        subtitle: `${item.theme_state} · ${item.participation_hint}`,
        summary: item.observation_summary,
      }));
    }
    if (addContextSource === "alert") {
      return (alertSummary?.items || []).map((item) => ({
        ref: `${item.ticker}|${item.alert_type}`,
        title: `${item.display_name} 提醒`,
        subtitle: `${item.alert_type} · ${item.priority}`,
        summary: item.next_action || item.body,
      }));
    }
    if (addContextSource === "decision_context_window") {
      return (decisionWindows?.items || []).map((item) => ({
        ref: String(item.window_id),
        title: `${item.display_name || item.ticker || item.topic_name || "研究对象"} 决策上下文`,
        subtitle: `${String(item.judgement_snapshot_json.action || "继续观察")} · ${item.window_size} 日窗口`,
        summary:
          item.summary ||
          [
            ...(item.support_events_json || []).slice(0, 1).map((event) => event.summary),
            ...(item.risk_events_json || []).slice(0, 1).map((event) => event.summary),
          ].join("；"),
      }));
    }
    if (addContextSource === "decision_outcome_review") {
      return (decisionReviews?.items || []).map((item) => ({
        ref: String(item.review_id),
        title: `${item.display_name} 结果回看`,
        subtitle: `${item.outcome_status} · ${item.review_horizon_days} 日`,
        summary: item.summary,
      }));
    }
    if (addContextSource === "risk_sizing") {
      const portfolioItem = riskSizingSummary?.available
        ? [
            {
              ref: "__portfolio__",
              title: "组合分仓建议",
              subtitle: `${riskSizingSummary.market_risk_level} · 组合层`,
              summary: riskSizingSummary.holding_risk_note,
            },
          ]
        : [];
      const tickerItems = (riskSizingSummary?.ticker_suggestions || []).map((item) => ({
        ref: item.ticker,
        title: `${item.display_name} 分仓建议`,
        subtitle: `${item.risk_level} · ${item.suggested_position_range}`,
        summary: item.summary,
      }));
      return [...portfolioItem, ...tickerItems];
    }
    if (addContextSource === "decision_effectiveness") {
      return decisionEffectiveness?.available
        ? [
            {
              ref: "__summary__",
              title: "近期判断有效性摘要",
              subtitle: `得分 ${decisionEffectiveness.overall_score} · ${decisionEffectiveness.review_count} 条`,
              summary: decisionEffectiveness.overall_summary,
            },
          ]
        : [];
    }
    return [];
  }, [
    addContextSource,
    alertSummary?.items,
    decisionEffectiveness,
    decisionReviews?.items,
    decisionWindows?.items,
    holdingOverview?.items,
    opportunityOverview?.items,
    riskSizingSummary,
    themeOverview?.items,
    tradingRuns?.runs,
    watchlistOverview?.items,
  ]);

  const handleCreateThread = async () => {
    if (!newTitle.trim()) {
      toast.error("请先填写线程标题");
      return;
    }
    try {
      const response = await createThread.mutateAsync({
        title: newTitle.trim(),
        focus_type: newFocusType,
        ticker_refs_json: splitRefs(newTickerRefs),
        theme_refs_json: splitRefs(newThemeRefs),
      });
      const created = response.data;
      setNewTitle("");
      setNewTickerRefs("");
      setNewThemeRefs("");
      setSearchParams({ threadId: String(created.thread_id) });
      toast.success("分析线程已创建");
    } catch {
      toast.error("创建分析线程失败");
    }
  };

  const handleRenameThread = (thread: StockAnalysisThread) => {
    setEditingThread(thread);
    setRenameTitle(thread.title);
    setRenameOpen(true);
  };

  const submitRenameThread = async () => {
    if (!editingThread || !renameTitle.trim()) {
      toast.error("请输入新的线程标题");
      return;
    }
    try {
      await updateThread.mutateAsync({
        threadId: editingThread.thread_id,
        data: { title: renameTitle.trim() },
      });
      setRenameOpen(false);
      setEditingThread(null);
      toast.success("线程标题已更新");
    } catch {
      toast.error("更新线程标题失败");
    }
  };

  const handleDeleteThread = async (threadId: number) => {
    try {
      await deleteThread.mutateAsync(threadId);
      if (selectedThreadId === threadId) {
        setSearchParams({});
      }
      toast.success("线程已归档");
    } catch {
      toast.error("归档线程失败");
    }
  };

  const handleDuplicateThread = async (threadId: number) => {
    try {
      const response = await duplicateThread.mutateAsync(threadId);
      setSearchParams({ threadId: String(response.data.thread.thread_id) });
      toast.success("研究线程已复制，可继续分叉研究");
    } catch {
      toast.error("复制线程失败");
    }
  };

  const handleTogglePin = async (contextId: number, isPinned: boolean) => {
    if (!currentThread) return;
    try {
      await updateContext.mutateAsync({
        threadId: currentThread.thread_id,
        contextId,
        data: { is_pinned: !isPinned },
      });
      toast.success(isPinned ? "已取消置顶" : "已置顶上下文卡片");
    } catch {
      toast.error("更新卡片状态失败");
    }
  };

  const handleDeleteContext = async (contextId: number) => {
    if (!currentThread) return;
    try {
      await deleteContext.mutateAsync({
        threadId: currentThread.thread_id,
        contextId,
      });
      toast.success("上下文卡片已删除");
    } catch {
      toast.error("删除上下文卡片失败");
    }
  };

  const persistCompareTargets = async (targets: StockAnalysisCompareTarget[]) => {
    if (!currentThread) return;
    await updateCompareTargets.mutateAsync({
      threadId: currentThread.thread_id,
      data: {
        compare_targets: normalizeCompareTargetsForSave(targets),
      },
    });
  };

  const handleAddCompareTarget = async (target: StockAnalysisCompareTarget) => {
    if (!currentThread) return;
    const exists = compareTargets.some(
      (item) => compareTargetKey(item) === compareTargetKey(target),
    );
    if (exists) {
      toast.message("该对象已在当前对比列表中");
      return;
    }
    try {
      await persistCompareTargets([...compareTargets, target]);
      toast.success("已加入当前对比对象");
    } catch {
      toast.error("加入对比失败");
    }
  };

  const handleRemoveCompareTarget = async (target: StockAnalysisCompareTarget) => {
    if (!currentThread) return;
    try {
      await persistCompareTargets(
        compareTargets.filter(
          (item) => compareTargetKey(item) !== compareTargetKey(target),
        ),
      );
      toast.success("已移出当前对比对象");
    } catch {
      toast.error("移出对比失败");
    }
  };

  const handleToggleForkSelect = (contextId: number) => {
    setForkSelectedContextIds((current) =>
      current.includes(contextId)
        ? current.filter((item) => item !== contextId)
        : [...current, contextId],
    );
  };

  const openForkDialog = (contextIds?: number[]) => {
    if (!currentThread) return;
    setForkTitle(
      compareTargets.length >= 2
        ? `${currentThread.title}（对比分叉）`
        : `${currentThread.title}（分叉）`,
    );
    setForkSelectedContextIds(contextIds || []);
    setIncludeCompareTargetsInFork(true);
    setPinImportedContexts(false);
    setSeedFromActiveMemory(false);
    setForkFocusTypeOverride("inherit");
    setForkDialogOpen(true);
  };

  const handleForkThread = async () => {
    if (!currentThread) return;
    try {
      const response = await forkThread.mutateAsync({
        threadId: currentThread.thread_id,
        data: {
          title: forkTitle.trim() || undefined,
          selected_context_ids: forkSelectedContextIds,
          include_compare_targets: includeCompareTargetsInFork,
          pin_imported_contexts: pinImportedContexts,
          seed_from_active_memory: seedFromActiveMemory,
          focus_type_override:
            forkFocusTypeOverride === "inherit" ? undefined : forkFocusTypeOverride,
        },
      });
      setForkDialogOpen(false);
      setSearchParams({ threadId: String(response.data.thread.thread_id) });
      toast.success("已创建分叉线程");
    } catch {
      toast.error("分叉线程失败");
    }
  };

  const handleCaptureThreadMemory = async () => {
    if (!currentThread) return;
    try {
      await captureThreadMemory.mutateAsync({
        threadId: currentThread.thread_id,
      });
      toast.success("已生成当前线程研究记忆");
    } catch {
      toast.error("生成研究记忆失败");
    }
  };

  const handleRefreshThreadMemory = async (memoryId: number) => {
    if (!currentThread) return;
    try {
      await refreshThreadMemory.mutateAsync({
        threadId: currentThread.thread_id,
        memoryId,
      });
      toast.success("已刷新当前线程研究记忆");
    } catch {
      toast.error("刷新研究记忆失败");
    }
  };

  const handleActivateThreadMemory = async (memoryId: number) => {
    if (!currentThread) return;
    try {
      await activateThreadMemory.mutateAsync({
        threadId: currentThread.thread_id,
        memoryId,
      });
      toast.success("已切换当前线程研究记忆");
    } catch {
      toast.error("切换研究记忆失败");
    }
  };

  const handleCaptureThreadCompression = async () => {
    if (!currentThread) return;
    try {
      await captureThreadCompression.mutateAsync({
        threadId: currentThread.thread_id,
      });
      toast.success("已整理当前线程对话");
    } catch {
      toast.error("整理当前对话失败");
    }
  };

  const handleRefreshThreadCompression = async (compressionId: number) => {
    if (!currentThread) return;
    try {
      await refreshThreadCompression.mutateAsync({
        threadId: currentThread.thread_id,
        compressionId,
      });
      toast.success("已刷新当前对话压缩摘要");
    } catch {
      toast.error("刷新对话压缩失败");
    }
  };

  const handleActivateThreadCompression = async (compressionId: number) => {
    if (!currentThread) return;
    try {
      await activateThreadCompression.mutateAsync({
        threadId: currentThread.thread_id,
        compressionId,
      });
      toast.success("已切换当前对话压缩摘要");
    } catch {
      toast.error("切换对话压缩失败");
    }
  };

  const handleGenerateResearchTasks = async () => {
    if (!currentThread) return;
    try {
      const response = await generateResearchTasks.mutateAsync({
        threadId: currentThread.thread_id,
      });
      toast.success(response.data.summary || "已从当前线程生成研究任务");
    } catch {
      toast.error("生成研究任务失败");
    }
  };

  const handleCreateResearchTask = async (draft: {
    title: string;
    summary: string;
    task_type: StockAnalysisResearchTask["task_type"];
    priority: StockAnalysisResearchTask["priority"];
    related_tickers_json: string[];
    related_themes_json: string[];
  }) => {
    if (!currentThread) return;
    try {
      await createResearchTask.mutateAsync({
        threadId: currentThread.thread_id,
        data: {
          ...draft,
          source_kind: "manual",
        },
      });
      toast.success("已创建手动研究任务");
    } catch {
      toast.error("创建研究任务失败");
    }
  };

  const handleCompleteResearchTask = async (taskId: number) => {
    if (!currentThread) return;
    try {
      await completeResearchTask.mutateAsync({
        threadId: currentThread.thread_id,
        taskId,
      });
      toast.success("已完成研究任务");
    } catch {
      toast.error("完成研究任务失败");
    }
  };

  const handleReopenResearchTask = async (taskId: number) => {
    if (!currentThread) return;
    try {
      await reopenResearchTask.mutateAsync({
        threadId: currentThread.thread_id,
        taskId,
      });
      toast.success("已重开研究任务");
    } catch {
      toast.error("重开研究任务失败");
    }
  };

  const handleDismissResearchTask = async (taskId: number) => {
    if (!currentThread) return;
    try {
      await dismissResearchTask.mutateAsync({
        threadId: currentThread.thread_id,
        taskId,
      });
      toast.success("已忽略研究任务");
    } catch {
      toast.error("忽略研究任务失败");
    }
  };

  const handleResearchFromTask = (task: StockAnalysisResearchTask) => {
    const prompt = [
      `围绕研究任务继续分析：${task.title}`,
      task.summary ? `重点：${task.summary}` : "",
      task.related_tickers_json.length
        ? `关注标的：${task.related_tickers_json.join("、")}`
        : "",
      task.related_themes_json.length
        ? `关注主题：${task.related_themes_json.join("、")}`
        : "",
    ]
      .filter(Boolean)
      .join("。");
    setActiveResearchTaskId(task.task_id);
    setMessageInput(prompt);
    toast.success(`已将任务 #${task.task_id} 设为本轮研究锚点`);
  };

  const applyRecentRefreshState = (refreshRun: StockAnalysisRefreshRunResult) => {
    setLastRefreshRun(refreshRun);
    setRecentContextRefreshState(
      Object.fromEntries(
        refreshRun.items.map((item) => [
          item.context_id,
          {
            status: item.status,
            reason: item.reason,
          },
        ]),
      ),
    );
  };

  const handleRefreshContext = async (contextId: number) => {
    if (!currentThread) return;
    try {
      const response = await refreshContext.mutateAsync({
        threadId: currentThread.thread_id,
        contextId,
      });
      const refreshed = response.data;
      applyRecentRefreshState({
        thread_id: currentThread.thread_id,
        refreshed_count: 1,
        skipped_count: 0,
        failed_count: 0,
        items: [
          {
            context_id: contextId,
            title: refreshed.title,
            source_module: refreshed.source_module,
            refresh_supported: refreshed.refresh_supported,
            status: "refreshed",
            reason: "单卡刷新成功",
            before_freshness_label: null,
            after_freshness_label: refreshed.freshness_label,
            changed_fields: ["generated_at"],
            new_generated_at: refreshed.generated_at,
            new_data_time: refreshed.data_time,
          },
        ],
        summary: `已刷新 1 张上下文卡片：${refreshed.title}`,
        generated_at: new Date().toISOString(),
        refreshed_context_ids: [contextId],
        skipped_context_ids: [],
        failed_context_ids: [],
        changed_contexts: [
          {
            context_id: contextId,
            title: refreshed.title,
            changed_fields: ["generated_at"],
            after_freshness_label: refreshed.freshness_label,
          },
        ],
      });
      toast.success("上下文卡片已刷新");
    } catch {
      toast.error("刷新上下文卡片失败");
    }
  };

  const handleRefreshStaleContexts = async () => {
    if (!currentThread) return null;
    try {
      const response = await refreshStaleContexts.mutateAsync({
        threadId: currentThread.thread_id,
        data: {
          include_supported_only: true,
          pin_refreshed_cards: false,
        },
      });
      applyRecentRefreshState(response.data);
      if (response.data.failed_count) {
        toast.warning(response.data.summary);
      } else {
        toast.success(response.data.summary);
      }
      return response.data;
    } catch {
      toast.error("批量刷新过期上下文失败");
      return null;
    }
  };

  const handleImportContext = async (sourceModule: string, sourceRef: string) => {
    if (!currentThread) {
      toast.error("请先选中线程");
      return;
    }
    try {
      await importContext.mutateAsync({
        source_module: sourceModule,
        source_ref: sourceRef,
        target_thread_id: currentThread.thread_id,
        mode: addContextMode,
      });
      toast.success("上下文卡片已加入当前线程");
      setAddContextOpen(false);
    } catch {
      toast.error("导入上下文失败");
    }
  };

  const handleSendMessage = async ({
    forceTooling = false,
    refreshBeforeAnswer = false,
    researchTaskId,
  }: {
    forceTooling?: boolean;
    refreshBeforeAnswer?: boolean;
    researchTaskId?: number | null;
  } = {}) => {
    if (!currentThread) {
      toast.error("请先选中线程");
      return;
    }
    if (!messageInput.trim()) {
      toast.error("请输入研究问题");
      return;
    }
    setPendingMessageAction(
      refreshBeforeAnswer ? "refresh" : forceTooling ? "tooling" : "send",
    );
    try {
      const response = await createMessage.mutateAsync({
        threadId: currentThread.thread_id,
        data: {
          message: messageInput.trim(),
          force_tooling: forceTooling,
          refresh_before_answer: refreshBeforeAnswer,
          research_task_id: researchTaskId ?? activeResearchTaskId ?? undefined,
        },
      });
      if (response.data.refreshed_before_answer && response.data.refresh_run_summary) {
        applyRecentRefreshState({
          thread_id: currentThread.thread_id,
          refreshed_count: response.data.refreshed_context_ids.length,
          skipped_count: response.data.refresh_skipped_context_ids.length,
          failed_count: response.data.refresh_failed_context_ids.length,
          items: [
            ...response.data.refreshed_context_ids.map((contextId) => ({
              context_id: contextId,
              title: contextTitleMap.get(contextId) || `上下文 #${contextId}`,
              source_module: "",
              refresh_supported: true,
              status: "refreshed" as const,
              reason: "回答前批量刷新成功",
              before_freshness_label: null,
              after_freshness_label: null,
              changed_fields: [],
              new_generated_at: null,
              new_data_time: null,
            })),
            ...response.data.refresh_skipped_context_ids.map((contextId) => ({
              context_id: contextId,
              title: contextTitleMap.get(contextId) || `上下文 #${contextId}`,
              source_module: "",
              refresh_supported: false,
              status: "skipped" as const,
              reason: "回答前批量刷新跳过",
              before_freshness_label: null,
              after_freshness_label: null,
              changed_fields: [],
              new_generated_at: null,
              new_data_time: null,
            })),
            ...response.data.refresh_failed_context_ids.map((contextId) => ({
              context_id: contextId,
              title: contextTitleMap.get(contextId) || `上下文 #${contextId}`,
              source_module: "",
              refresh_supported: true,
              status: "failed" as const,
              reason: "回答前批量刷新失败",
              before_freshness_label: null,
              after_freshness_label: null,
              changed_fields: [],
              new_generated_at: null,
              new_data_time: null,
            })),
          ],
          summary: response.data.refresh_run_summary,
          generated_at: new Date().toISOString(),
          refreshed_context_ids: response.data.refreshed_context_ids,
          skipped_context_ids: response.data.refresh_skipped_context_ids,
          failed_context_ids: response.data.refresh_failed_context_ids,
          changed_contexts: response.data.refresh_changed_contexts.map((item) => ({
            context_id: Number(item.context_id || 0),
            title:
              typeof item.title === "string"
                ? item.title
                : contextTitleMap.get(Number(item.context_id || 0)) ||
                  `上下文 #${String(item.context_id || "")}`,
            changed_fields: Array.isArray(item.changed_fields) ? item.changed_fields : [],
            after_freshness_label:
              typeof item.after_freshness_label === "string"
                ? item.after_freshness_label
                : null,
          })),
        });
      }
      setMessageInput("");
      setActiveResearchTaskId(null);
      toast.success("研究消息已发送");
    } catch {
      toast.error("发送消息失败");
    } finally {
      setPendingMessageAction(null);
    }
  };

  const handleSaveEvidence = async (
    messageId: string,
    evidenceIndex: number,
    title?: string,
  ) => {
    if (!currentThread) {
      toast.error("请先选中线程");
      return;
    }
    try {
      await saveEvidence.mutateAsync({
        threadId: currentThread.thread_id,
        messageId,
        data: { evidence_index: evidenceIndex, title, pin: false },
      });
      toast.success("临时证据已保存为上下文卡片");
    } catch {
      toast.error("保存临时证据失败");
    }
  };

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-semibold text-2xl">股票分析工作区</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            默认先基于当前显式上下文卡片和线程历史回答；当信息不足或你显式点击补数按钮时，再补临时证据，不自动保存为长期上下文。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to="/agent/TradingAgents">去 TradingAgents</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/daily-workbench">回到总控台</Link>
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex min-h-96 items-center justify-center">
          <Spinner className="size-6" />
        </div>
      ) : null}

      {!isLoading && (isError || !overview) ? (
        <div className="rounded-xl border border-dashed p-6 text-muted-foreground text-sm">
          当前无法加载股票分析工作区，请稍后再试。
        </div>
      ) : null}

      {!isLoading && !isError && overview ? (
        <div className="grid min-h-0 flex-1 gap-4 xl:grid-cols-[320px_minmax(0,1fr)_360px]">
          <Card className="min-h-0">
            <CardHeader>
              <CardTitle>研究线程</CardTitle>
              <CardDescription>显式管理研究主题、焦点和 conversation 绑定。</CardDescription>
            </CardHeader>
            <CardContent className="flex min-h-0 flex-1 flex-col gap-4">
              <div className="space-y-3 rounded-xl border p-3">
                <Input
                  value={newTitle}
                  onChange={(event) => setNewTitle(event.target.value)}
                  placeholder="例如：追问 AI 算力主线分歧"
                />
                <Select value={newFocusType} onValueChange={setNewFocusType}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="选择 focus_type" />
                  </SelectTrigger>
                  <SelectContent>
                    {FOCUS_OPTIONS.map((option) => (
                      <SelectItem key={option} value={option}>
                        {option}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  value={newTickerRefs}
                  onChange={(event) => setNewTickerRefs(event.target.value)}
                  placeholder="ticker refs，逗号分隔"
                />
                <Input
                  value={newThemeRefs}
                  onChange={(event) => setNewThemeRefs(event.target.value)}
                  placeholder="theme refs，逗号分隔"
                />
                <Button
                  className="w-full"
                  onClick={handleCreateThread}
                  disabled={createThread.isPending}
                >
                  {createThread.isPending ? "创建中..." : "新建分析线程"}
                </Button>
              </div>

              <div className="scroll-container min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
                {threads.length ? (
                  threads.map((thread) => (
                    <div
                      key={thread.thread_id}
                      className={`rounded-xl border p-3 ${
                        currentThread?.thread_id === thread.thread_id
                          ? "border-primary bg-primary/5"
                          : "bg-background"
                      }`}
                    >
                      <button
                        type="button"
                        className="w-full text-left"
                        onClick={() =>
                          setSearchParams({ threadId: String(thread.thread_id) })
                        }
                      >
                        <div className="flex items-center justify-between gap-2">
                          <p className="font-medium text-sm">{thread.title}</p>
                          <Badge variant="outline">{thread.focus_type}</Badge>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2 text-muted-foreground text-xs">
                          <span>更新于 {formatTime(thread.updated_at)}</span>
                          <span>{thread.context_count} 张上下文卡片</span>
                        </div>
                      </button>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleRenameThread(thread)}
                        >
                          重命名
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDuplicateThread(thread.thread_id)}
                        >
                          <Copy className="size-4" />
                          复制
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDeleteThread(thread.thread_id)}
                        >
                          <Trash2 className="size-4" />
                          删除
                        </Button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                    {overview.empty_message}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="min-h-0">
            <CardHeader>
              <CardTitle>当前线程主区</CardTitle>
              <CardDescription>默认先回答；信息不足或你主动触发时，再进入补数模式。</CardDescription>
            </CardHeader>
            <CardContent className="flex min-h-0 flex-1 flex-col gap-4">
              {currentThread ? (
                <>
                  <div className="rounded-xl border p-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold text-lg">{currentThread.title}</p>
                      <Badge variant="secondary">{currentThread.focus_type}</Badge>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {currentThread.ticker_refs_json.map((item) => (
                        <Button
                          key={item}
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            void handleAddCompareTarget(buildManualCompareTarget("ticker", item))
                          }
                        >
                          {item}
                        </Button>
                      ))}
                      {currentThread.theme_refs_json.map((item) => (
                        <Button
                          key={item}
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            void handleAddCompareTarget(buildManualCompareTarget("theme", item))
                          }
                        >
                          {item}
                        </Button>
                      ))}
                    </div>
                    <p className="mt-2 text-muted-foreground text-xs">
                      点击 ticker / theme 可直接加入当前 compare targets。
                    </p>
                  </div>

                  <div className="rounded-xl border p-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="secondary">默认模式：context_only</Badge>
                      <Badge variant="outline">可切换：need_tooling / user_forced_tooling</Badge>
                      <Badge variant="outline">
                        conversation_id: {currentThread.conversation_id}
                      </Badge>
                    </div>
                  </div>

                  <StockAnalysisCompareTray
                    compareTargets={compareTargets}
                    isMutating={updateCompareTargets.isPending}
                    onFork={() => openForkDialog()}
                    onRemove={(target) => void handleRemoveCompareTarget(target)}
                  />

                  <StockAnalysisThreadSummary
                    compareTargetCount={compareTargets.length}
                    staleCount={staleContextCount}
                    refreshRecommendedCount={refreshRecommendedCount}
                    savedEvidenceCount={savedEvidenceCount}
                    activeMemoryAvailable={!!activeMemory}
                    activeCompressionAvailable={!!activeCompression}
                    compressionRecommended={
                      compressionData?.compression_recommended || false
                    }
                    activeCompressionStale={
                      compressionData?.active_compression_stale || false
                    }
                    uncompressedMessageCount={
                      compressionData?.uncompressed_message_count || 0
                    }
                    compressionReason={compressionData?.compression_reason || null}
                    openResearchTaskCount={researchTaskData?.open_count || 0}
                    highPriorityResearchTaskCount={
                      researchTaskData?.high_priority_open_count || 0
                    }
                    relatedTaskCount={latestRelatedTaskIds.length}
                    lastResearchTaskGenerateAt={
                      researchTaskData?.last_generated_at || null
                    }
                    hasActionableTaskGap={
                      researchTaskData?.has_actionable_gap || false
                    }
                    actionableTaskGapSummary={
                      researchTaskData?.actionable_gap_summary || null
                    }
                    lastExecutionTriggeredRefresh={
                      Boolean(latestAssistantMessage?.refreshed_before_answer) ||
                      latestExecutedStepTypes.includes("refresh_stale_contexts")
                    }
                    lastExecutionTriggeredTooling={
                      latestExecutedStepTypes.some((item) =>
                        item.startsWith("collect_"),
                      )
                    }
                    lastExecutionTriggeredValidation={Boolean(latestValidationSummary)}
                    lastValidationSummary={latestValidationSummaryText}
                    lastRefreshAt={lastRefreshRun?.generated_at || null}
                    lastRefreshSummary={lastRefreshRun?.summary || null}
                  />

                  <StockAnalysisMemoryPanel
                    activeMemory={activeMemory}
                    memories={threadMemories.filter(
                      (item) => item.memory_id !== activeMemory?.memory_id,
                    )}
                    isLoading={memoriesLoading}
                    onCapture={() => void handleCaptureThreadMemory()}
                    onRefresh={(memoryId) => void handleRefreshThreadMemory(memoryId)}
                    onActivate={(memoryId) => void handleActivateThreadMemory(memoryId)}
                    capturePending={captureThreadMemory.isPending}
                    refreshPending={refreshThreadMemory.isPending}
                    activatePending={activateThreadMemory.isPending}
                  />

                  <StockAnalysisCompressionPanel
                    activeCompression={activeCompression}
                    compressions={threadCompressions.filter(
                      (item) =>
                        item.compression_id !== activeCompression?.compression_id,
                    )}
                    compressionRecommended={
                      compressionData?.compression_recommended || false
                    }
                    compressionReason={compressionData?.compression_reason || null}
                    uncompressedMessageCount={
                      compressionData?.uncompressed_message_count || 0
                    }
                    estimatedHistorySize={
                      compressionData?.estimated_history_size || 0
                    }
                    activeCompressionStale={
                      compressionData?.active_compression_stale || false
                    }
                    isLoading={compressionsLoading}
                    onCapture={() => void handleCaptureThreadCompression()}
                    onRefresh={(compressionId) =>
                      void handleRefreshThreadCompression(compressionId)
                    }
                    onActivate={(compressionId) =>
                      void handleActivateThreadCompression(compressionId)
                    }
                    capturePending={captureThreadCompression.isPending}
                    refreshPending={refreshThreadCompression.isPending}
                    activatePending={activateThreadCompression.isPending}
                  />

                  <StockAnalysisResearchTaskPanel
                    taskData={researchTaskData}
                    currentFocusTickers={latestFocusTickers}
                    currentFocusThemes={latestFocusThemes}
                    relatedTaskIds={latestRelatedTaskIds}
                    isLoading={researchTasksLoading}
                    generatePending={generateResearchTasks.isPending}
                    createPending={createResearchTask.isPending}
                    actionPending={
                      completeResearchTask.isPending ||
                      reopenResearchTask.isPending ||
                      dismissResearchTask.isPending
                    }
                    onGenerate={() => void handleGenerateResearchTasks()}
                    onCreate={(draft) => void handleCreateResearchTask(draft)}
                    onResearch={(task) => void handleResearchFromTask(task)}
                    onComplete={(task) => void handleCompleteResearchTask(task.task_id)}
                    onReopen={(task) => void handleReopenResearchTask(task.task_id)}
                    onDismiss={(task) => void handleDismissResearchTask(task.task_id)}
                  />

                  <StockAnalysisRefreshSummary refreshRun={lastRefreshRun} />

                  <div className="flex min-h-0 flex-1 flex-col rounded-xl border p-4">
                    <p className="font-medium text-sm">研究线程聊天</p>
                    <div className="mt-3 flex min-h-0 flex-1 flex-col gap-3">
                      <div className="scroll-container flex-1 space-y-3 overflow-y-auto rounded-xl border p-4">
                        {messagesLoading ? (
                          <div className="flex min-h-40 items-center justify-center">
                            <Spinner className="size-5" />
                          </div>
                        ) : messages?.items.length ? (
                          messages.items.map((item) => (
                            <div
                              key={item.item_id}
                              className={`rounded-xl border p-3 ${
                                isAssistantRole(item.role)
                                  ? "bg-primary/5"
                                  : "bg-background"
                              }`}
                            >
                              <div className="flex flex-wrap items-center gap-2">
                                <Badge variant="outline">
                                  {isAssistantRole(item.role) ? "研究助手" : "用户"}
                                </Badge>
                                {isAssistantRole(item.role) ? (
                                  <>
                                    <Badge variant="secondary">{item.answer_basis}</Badge>
                                    <Badge variant="outline">模式：{item.mode}</Badge>
                                    <Badge variant="outline">
                                      使用上下文 {item.used_context_ids.length} 张
                                    </Badge>
                                    {item.comparison_mode ? (
                                      <Badge variant="outline">comparison</Badge>
                                    ) : null}
                                  </>
                                ) : null}
                              </div>
                              <p className="mt-3 whitespace-pre-wrap text-sm">{item.content}</p>
                              {isAssistantRole(item.role) ? (
                                <div className="mt-3 space-y-3">
                                  {item.compared_tickers.length ||
                                  item.stale_context_ids.length ||
                                  item.refresh_recommended_context_ids.length ? (
                                    <div className="rounded-lg border border-dashed p-3 text-sm">
                                      <p className="font-medium">本轮比较与时效提示</p>
                                      <div className="mt-2 flex flex-wrap gap-2">
                                        {item.compared_tickers.map((ticker) => (
                                          <Badge key={ticker} variant="outline">
                                            比较对象：{ticker}
                                          </Badge>
                                        ))}
                                      </div>
                                      {item.stale_context_ids.length ? (
                                        <p className="mt-2 text-muted-foreground text-xs">
                                          较旧对象：
                                          {item.stale_context_ids
                                            .map(
                                              (contextId) =>
                                                contextTitleMap.get(contextId) ||
                                                `上下文 #${contextId}`,
                                            )
                                            .join("、")}
                                        </p>
                                      ) : null}
                                      {item.refresh_recommended_context_ids.length ? (
                                        <p className="mt-1 text-muted-foreground text-xs">
                                          建议刷新后再聊：
                                          {item.refresh_recommended_context_ids
                                            .map(
                                              (contextId) =>
                                                contextTitleMap.get(contextId) ||
                                                `上下文 #${contextId}`,
                                            )
                                            .join("、")}
                                        </p>
                                      ) : null}
                                    </div>
                                  ) : null}
                                  {item.refreshed_before_answer ? (
                                    <div className="rounded-lg border border-dashed p-3 text-sm">
                                      <p className="font-medium">回答前刷新结果</p>
                                      <p className="mt-1 text-muted-foreground">
                                        {item.refresh_run_summary ||
                                          `本轮回答前已刷新 ${item.refreshed_context_ids.length} 张上下文。`}
                                      </p>
                                      <div className="mt-2 flex flex-wrap gap-2">
                                        {item.refresh_changed_contexts.map((context) => {
                                          const title =
                                            typeof context.title === "string"
                                              ? context.title
                                              : `上下文 #${String(context.context_id || "")}`;
                                          const changedFields = Array.isArray(
                                            context.changed_fields,
                                          )
                                            ? context.changed_fields.join(", ")
                                            : "";
                                          return (
                                            <Badge
                                              key={`${title}-${changedFields}`}
                                              variant="outline"
                                              className="whitespace-normal"
                                            >
                                              {title}: {changedFields || "no material change"}
                                            </Badge>
                                          );
                                        })}
                                      </div>
                                      {item.refresh_failed_context_ids.length ? (
                                        <p className="mt-2 text-muted-foreground text-xs">
                                          刷新失败：
                                          {item.refresh_failed_context_ids
                                            .map(
                                              (contextId) =>
                                                contextTitleMap.get(contextId) ||
                                                `上下文 #${contextId}`,
                                            )
                                            .join("、")}
                                        </p>
                                      ) : null}
                                      {item.refresh_skipped_context_ids.length ? (
                                        <p className="mt-1 text-muted-foreground text-xs">
                                          被跳过：
                                          {item.refresh_skipped_context_ids
                                            .map(
                                              (contextId) =>
                                                contextTitleMap.get(contextId) ||
                                                `上下文 #${contextId}`,
                                            )
                                            .join("、")}
                                        </p>
                                      ) : null}
                                    </div>
                                  ) : null}
                                  {item.question_intent ||
                                  item.response_strategy ||
                                  item.recommended_next_action ? (
                                    <div className="rounded-lg border border-dashed p-3 text-sm">
                                      <p className="font-medium">问题路由说明</p>
                                      <div className="mt-2 flex flex-wrap gap-2">
                                        {item.question_intent ? (
                                          <Badge variant="secondary">
                                            问题类型：{item.question_intent}
                                          </Badge>
                                        ) : null}
                                        {item.response_strategy ? (
                                          <Badge variant="outline">
                                            回答策略：{item.response_strategy}
                                          </Badge>
                                        ) : null}
                                      </div>
                                      <p className="mt-2 text-muted-foreground">
                                        {item.routing_reason || "当前未提供额外路由说明。"}
                                      </p>
                                      {item.recommended_next_action ? (
                                        <p className="mt-2 text-sm">
                                          下一步建议：{item.recommended_next_action}
                                        </p>
                                      ) : null}
                                      {item.suggested_task_titles.length ? (
                                        <div className="mt-2 flex flex-wrap gap-2">
                                          {item.suggested_task_titles.map((title) => (
                                            <Badge
                                              key={title}
                                              variant="outline"
                                              className="whitespace-normal"
                                            >
                                              {title}
                                            </Badge>
                                          ))}
                                        </div>
                                      ) : null}
                                    </div>
                                  ) : null}
                                  <StockAnalysisExecutionTrace
                                    questionIntent={item.question_intent}
                                    responseStrategy={item.response_strategy}
                                    executionPlanSummary={item.execution_plan_summary}
                                    executedSteps={item.executed_steps}
                                    skippedSteps={item.skipped_steps}
                                    failedSteps={item.failed_steps}
                                  />
                                  <StockAnalysisValidationSummary
                                    validationSummary={item.validation_summary}
                                    thesisChangeHint={item.thesis_change_hint}
                                  />
                                  {item.related_task_ids.length ||
                                  item.task_update_suggestions.length ? (
                                    <div className="rounded-lg border border-dashed p-3 text-sm">
                                      <p className="font-medium">Research Task 建议</p>
                                      {item.related_task_ids.length ? (
                                        <p className="mt-2 text-muted-foreground">
                                          本轮关联任务：{item.related_task_ids.join("、")}
                                        </p>
                                      ) : null}
                                      {item.task_update_suggestions.length ? (
                                        <div className="mt-2 space-y-2">
                                          {item.task_update_suggestions.map((suggestion, index) => (
                                            <div
                                              key={`${String(suggestion.task_id || index)}-${String(
                                                suggestion.suggestion || "",
                                              )}`}
                                              className="rounded border p-2"
                                            >
                                              <p>
                                                任务 #{String(suggestion.task_id || "--")}：
                                                {String(suggestion.suggestion || "keep_open")}
                                              </p>
                                              <p className="mt-1 text-muted-foreground text-xs">
                                                {String(suggestion.reason || "")}
                                              </p>
                                            </div>
                                          ))}
                                        </div>
                                      ) : null}
                                    </div>
                                  ) : null}
                                  {item.used_active_memory ? (
                                    <div className="rounded-lg border border-dashed p-3 text-sm">
                                      <p className="font-medium">研究记忆使用说明</p>
                                      <p className="mt-1 text-muted-foreground">
                                        本轮回答参考了当前线程研究记忆
                                        {item.active_memory_title
                                          ? `：${item.active_memory_title}`
                                          : ""}
                                        {item.active_memory_version
                                          ? ` · v${item.active_memory_version}`
                                          : ""}
                                        {item.active_memory_updated_at
                                          ? ` · 更新于 ${formatTime(item.active_memory_updated_at)}`
                                          : ""}
                                      </p>
                                    </div>
                                  ) : null}
                                  {item.used_active_compression ? (
                                    <div className="rounded-lg border border-dashed p-3 text-sm">
                                      <p className="font-medium">对话压缩使用说明</p>
                                      <p className="mt-1 text-muted-foreground">
                                        本轮回答参考了当前线程对话压缩摘要
                                        {item.active_compression_title
                                          ? `：${item.active_compression_title}`
                                          : ""}
                                        {item.active_compression_version
                                          ? ` · v${item.active_compression_version}`
                                          : ""}
                                        {item.active_compression_updated_at
                                          ? ` · 更新于 ${formatTime(item.active_compression_updated_at)}`
                                          : ""}
                                        {item.active_compression_covered_until_message_id
                                          ? ` · 覆盖到 ${item.active_compression_covered_until_message_id}`
                                          : ""}
                                        {typeof item.active_compression_covered_message_count ===
                                        "number"
                                          ? ` · 覆盖 ${item.active_compression_covered_message_count} 条消息`
                                          : ""}
                                        {item.recent_raw_message_count
                                          ? ` · 保留最近 ${item.recent_raw_message_count} 条原始消息`
                                          : ""}
                                      </p>
                                    </div>
                                  ) : null}
                                  {item.tool_reason ? (
                                    <div className="rounded-lg border border-dashed p-3 text-sm">
                                      <p className="font-medium">回答依据说明</p>
                                      <p className="mt-1 text-muted-foreground">
                                        {item.tool_reason}
                                      </p>
                                    </div>
                                  ) : null}
                                  {(item.tool_calls_summary.length ||
                                    item.unavailable_tools.length ||
                                    item.temporary_evidence_blocks.length) ? (
                                    <details className="rounded-lg border p-3 text-sm">
                                      <summary className="cursor-pointer font-medium">
                                        工具调用说明区
                                      </summary>
                                      <div className="mt-3 space-y-3 text-muted-foreground">
                                        {item.tool_calls_summary.length ? (
                                          <div>
                                            <p className="font-medium text-foreground">
                                              已补哪些数据
                                            </p>
                                            <div className="mt-2 flex flex-wrap gap-2">
                                              {item.tool_calls_summary.map((summary) => (
                                                <Badge
                                                  key={summary}
                                                  variant="outline"
                                                  className="whitespace-normal"
                                                >
                                                  {summary}
                                                </Badge>
                                              ))}
                                            </div>
                                          </div>
                                        ) : null}
                                        {item.used_internal_sources.length ||
                                        item.used_external_sources.length ? (
                                          <div className="space-y-2">
                                            {item.used_internal_sources.length ? (
                                              <div>
                                                <p className="font-medium text-foreground">
                                                  内部来源
                                                </p>
                                                <div className="mt-2 flex flex-wrap gap-2">
                                                  {item.used_internal_sources.map((source) => (
                                                    <Badge
                                                      key={source}
                                                      variant="outline"
                                                      className="whitespace-normal"
                                                    >
                                                      {source}
                                                    </Badge>
                                                  ))}
                                                </div>
                                              </div>
                                            ) : null}
                                            {item.used_external_sources.length ? (
                                              <div>
                                                <p className="font-medium text-foreground">
                                                  外部来源
                                                </p>
                                                <div className="mt-2 flex flex-wrap gap-2">
                                                  {item.used_external_sources.map((source) => (
                                                    <Badge
                                                      key={source}
                                                      variant="outline"
                                                      className="whitespace-normal"
                                                    >
                                                      {source}
                                                    </Badge>
                                                  ))}
                                                </div>
                                              </div>
                                            ) : null}
                                          </div>
                                        ) : null}
                                        {item.provider_attempts.length ? (
                                          <div className="space-y-2">
                                            <p className="font-medium text-foreground">
                                              外部 provider 编排
                                            </p>
                                            <div className="flex flex-wrap gap-2">
                                              {item.provider_attempts.map((attempt, index) => (
                                                <Badge
                                                  key={`${index}-${String(attempt.provider)}`}
                                                  variant="outline"
                                                  className="whitespace-normal"
                                                >
                                                  {String(attempt.tool)} / {String(attempt.provider)} /{" "}
                                                  {String(attempt.status)}
                                                  {attempt.reason
                                                    ? `: ${String(attempt.reason)}`
                                                    : ""}
                                                </Badge>
                                              ))}
                                            </div>
                                            {item.provider_used.length ? (
                                              <p className="text-xs">
                                                成功 provider：{item.provider_used.join(" -> ")}
                                              </p>
                                            ) : null}
                                            {item.provider_fallback_chain.length ? (
                                              <p className="text-xs">
                                                fallback chain：
                                                {item.provider_fallback_chain.join(" -> ")}
                                              </p>
                                            ) : null}
                                          </div>
                                        ) : null}
                                        {item.evidence_generated_at || item.evidence_staleness_hint ? (
                                          <div className="space-y-2">
                                            <p className="font-medium text-foreground">
                                              证据时间与时效
                                            </p>
                                            <div className="flex flex-wrap gap-2">
                                              {item.evidence_generated_at ? (
                                                <Badge variant="outline">
                                                  生成时间：{formatTime(item.evidence_generated_at)}
                                                </Badge>
                                              ) : null}
                                              {item.evidence_generated_at ? (
                                                <Badge variant="outline">
                                                  {resolveFreshnessLabel(item.evidence_generated_at) ||
                                                    "时效待确认"}
                                                </Badge>
                                              ) : null}
                                            </div>
                                            {item.evidence_staleness_hint ? (
                                              <p className="text-xs">
                                                {item.evidence_staleness_hint}
                                              </p>
                                            ) : null}
                                          </div>
                                        ) : null}
                                        {item.unavailable_tools.length ? (
                                          <div>
                                            <p className="font-medium text-foreground">
                                              不可用工具
                                            </p>
                                            <div className="mt-2 flex flex-wrap gap-2">
                                              {item.unavailable_tools.map((tool) => (
                                                <Badge
                                                  key={`${tool.tool}-${tool.reason}`}
                                                  variant="outline"
                                                  className="whitespace-normal"
                                                >
                                                  {tool.tool}: {tool.reason}
                                                </Badge>
                                              ))}
                                            </div>
                                          </div>
                                        ) : null}
                                        {item.temporary_evidence_blocks.length ? (
                                          <div>
                                            <p className="font-medium text-foreground">
                                              临时证据补充
                                            </p>
                                            <div className="mt-2 space-y-2">
                                              {item.temporary_evidence_blocks.map((block, evidenceIndex) => (
                                                <div
                                                  key={block.evidence_id || `${block.title}-${block.summary}`}
                                                  className="rounded-lg border border-dashed p-3"
                                                >
                                                  <div className="flex flex-wrap items-center gap-2">
                                                    <p className="font-medium text-foreground">
                                                      {block.title}
                                                    </p>
                                                    <Badge variant="outline">
                                                      {block.temporary
                                                        ? "temporary=true"
                                                        : "temporary=false"}
                                                    </Badge>
                                                    {block.source_label ? (
                                                      <Badge variant="outline">
                                                        来源：{block.source_label}
                                                      </Badge>
                                                    ) : null}
                                                    {block.is_external ? (
                                                      <Badge variant="outline">外部补数</Badge>
                                                    ) : (
                                                      <Badge variant="outline">内部/行情补数</Badge>
                                                    )}
                                                    {block.data_time ? (
                                                      <Badge variant="outline">
                                                        数据时间：{formatTime(block.data_time)}
                                                      </Badge>
                                                    ) : null}
                                                    {block.data_time ? (
                                                      <Badge variant="outline">
                                                        {resolveFreshnessLabel(block.data_time) ||
                                                          "时效待确认"}
                                                      </Badge>
                                                    ) : null}
                                                  </div>
                                                  <p className="mt-1">{block.summary}</p>
                                                  {block.staleness_hint ? (
                                                    <p className="mt-2 text-muted-foreground text-xs">
                                                      {block.staleness_hint}
                                                    </p>
                                                  ) : null}
                                                  <div className="mt-3 flex flex-wrap gap-2">
                                                    {(block.ticker_refs_json || []).map((ref) => (
                                                      <Badge key={ref} variant="outline">
                                                        {ref}
                                                      </Badge>
                                                    ))}
                                                    {(block.theme_refs_json || []).map((ref) => (
                                                      <Badge key={ref} variant="outline">
                                                        {ref}
                                                      </Badge>
                                                    ))}
                                                  </div>
                                                  <div className="mt-3 flex flex-wrap gap-2">
                                                    <Button
                                                      size="sm"
                                                      variant="outline"
                                                      disabled={saveEvidence.isPending}
                                                      onClick={() =>
                                                        void handleSaveEvidence(
                                                          item.item_id,
                                                          evidenceIndex,
                                                          block.title,
                                                        )
                                                      }
                                                    >
                                                      保存为上下文
                                                    </Button>
                                                  </div>
                                                </div>
                                              ))}
                                            </div>
                                          </div>
                                        ) : null}
                                        <p className="text-xs">
                                          以上证据仅用于本轮回答，未自动保存为长期上下文。
                                        </p>
                                      </div>
                                    </details>
                                  ) : null}
                                </div>
                              ) : null}
                              {item.missing_context_hints.length ? (
                                <div className="mt-3 flex flex-wrap gap-2">
                                  {item.missing_context_hints.map((hint) => (
                                    <Badge key={hint} variant="outline" className="whitespace-normal">
                                      {hint}
                                    </Badge>
                                  ))}
                                </div>
                              ) : null}
                            </div>
                          ))
                        ) : (
                          <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                            当前线程还没有历史消息。可以直接基于右侧已挂载的上下文卡片开始提问。
                          </div>
                        )}
                        {createMessage.isPending ? (
                          <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                            {pendingMessageAction === "refresh"
                              ? "正在刷新过期上下文并重新生成回答..."
                              : pendingMessageAction === "tooling"
                                ? "正在补数据并生成回答..."
                                : "正在基于当前上下文生成回答..."}
                          </div>
                        ) : null}
                      </div>
                      {activeResearchTaskId ? (
                        <div className="flex flex-wrap items-center gap-2 rounded-lg border border-dashed p-3 text-sm">
                          <Badge variant="secondary">当前研究锚点任务 #{activeResearchTaskId}</Badge>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setActiveResearchTaskId(null)}
                          >
                            清除锚点
                          </Button>
                        </div>
                      ) : null}
                      <Textarea
                        value={messageInput}
                        onChange={(event) => setMessageInput(event.target.value)}
                        placeholder="例如：先比较当前线程里这几只票的优先级；若长期上下文偏旧，可点“刷新过期上下文后再回答”。"
                        className="min-h-24"
                      />
                      <p className="text-muted-foreground text-xs">
                        `发送` 只基于当前上下文；`补数据后再回答` 会拉临时证据；`刷新过期上下文后再回答` 会先更新长期上下文。
                      </p>
                      <div className="flex flex-wrap justify-end gap-2">
                        <Button
                          variant="outline"
                          onClick={() => openForkDialog()}
                          disabled={forkThread.isPending}
                        >
                          <Zap className="size-4" />
                          分叉线程
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => void handleSendMessage({ forceTooling: true })}
                          disabled={createMessage.isPending}
                        >
                          {pendingMessageAction === "tooling" && createMessage.isPending
                            ? "补数中..."
                            : "补数据后再回答"}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => void handleSendMessage({ refreshBeforeAnswer: true })}
                          disabled={createMessage.isPending || refreshStaleContexts.isPending}
                        >
                          <RefreshCw className="size-4" />
                          {pendingMessageAction === "refresh" && createMessage.isPending
                            ? "刷新并重答中..."
                            : "刷新过期上下文后再回答"}
                        </Button>
                        <Button
                          onClick={() => void handleSendMessage()}
                          disabled={createMessage.isPending}
                        >
                          <Send className="size-4" />
                          {pendingMessageAction === "send" && createMessage.isPending
                            ? "生成中..."
                            : "发送"}
                        </Button>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="rounded-xl border border-dashed p-6 text-muted-foreground text-sm">
                  还没有选中线程，先在左侧创建一个分析线程，或从 TradingAgents 导入现有 run。
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="min-h-0">
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle>上下文卡片</CardTitle>
                  <CardDescription>
                    统一管理基础上下文和高级研究卡片；长期挂载仍必须显式导入。
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => void handleRefreshStaleContexts()}
                    disabled={!currentThread || refreshStaleContexts.isPending}
                  >
                    <RefreshCw className="size-4" />
                    {refreshStaleContexts.isPending ? "刷新中..." : "刷新过期上下文"}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => openForkDialog()}
                    disabled={!currentThread}
                  >
                    <Zap className="size-4" />
                    分叉线程
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setAddContextOpen(true)}
                    disabled={!currentThread}
                  >
                    <Plus className="size-4" />
                    添加上下文
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="scroll-container min-h-0 flex-1 space-y-3 overflow-y-auto">
              {!currentThread ? (
                <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                  先选中线程，再查看或管理上下文卡片。
                </div>
              ) : contextsLoading ? (
                <div className="flex min-h-48 items-center justify-center">
                  <Spinner className="size-5" />
                </div>
              ) : contextItems.length ? (
                contextItems.map((item) => {
                  const compareTarget = buildCompareTargetFromCard(item);
                  const inCompare = compareTarget
                    ? compareTargetKeySet.has(compareTargetKey(compareTarget))
                    : false;
                  return (
                    <StockAnalysisContextCard
                      key={item.context_id}
                      item={item}
                      isSelectedForFork={forkSelectedContextIds.includes(item.context_id)}
                      isInCompare={inCompare}
                      recentRefreshState={recentContextRefreshState[item.context_id] || null}
                      onToggleSelect={handleToggleForkSelect}
                      onTogglePin={handleTogglePin}
                      onDelete={handleDeleteContext}
                      onRefresh={(contextId) => void handleRefreshContext(contextId)}
                      onAddToCompare={(card) => {
                        const target = buildCompareTargetFromCard(card);
                        if (!target) {
                          toast.error("该卡片缺少可加入对比的 ticker 或 theme");
                          return;
                        }
                        void handleAddCompareTarget(target);
                      }}
                      onRemoveFromCompare={(card) => {
                        const target = buildCompareTargetFromCard(card);
                        if (!target) return;
                        void handleRemoveCompareTarget(target);
                      }}
                      onForkSingle={(card) => openForkDialog([card.context_id])}
                    />
                  );
                })
              ) : (
                <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                  当前线程还没有上下文卡片。可先从 TradingAgents、机会池、观察池、持仓、题材雷达、提醒或高级研究卡片导入。
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      ) : null}

      <Dialog open={renameOpen} onOpenChange={setRenameOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>重命名分析线程</DialogTitle>
            <DialogDescription>只更新线程标题，不改 conversation 历史。</DialogDescription>
          </DialogHeader>
          <Input
            value={renameTitle}
            onChange={(event) => setRenameTitle(event.target.value)}
            placeholder="输入新的线程标题"
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setRenameOpen(false)}>
              取消
            </Button>
            <Button onClick={submitRenameThread} disabled={updateThread.isPending}>
              {updateThread.isPending ? "保存中..." : "保存"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <StockAnalysisForkDialog
        open={forkDialogOpen}
        onOpenChange={setForkDialogOpen}
        title={forkTitle}
        onTitleChange={setForkTitle}
        selectedContextCount={forkSelectedContextIds.length}
        includeCompareTargets={includeCompareTargetsInFork}
        onIncludeCompareTargetsChange={setIncludeCompareTargetsInFork}
        pinImportedContexts={pinImportedContexts}
        onPinImportedContextsChange={setPinImportedContexts}
        seedFromActiveMemory={seedFromActiveMemory}
        onSeedFromActiveMemoryChange={setSeedFromActiveMemory}
        hasActiveMemory={!!activeMemory}
        focusTypeOverride={forkFocusTypeOverride}
        onFocusTypeOverrideChange={setForkFocusTypeOverride}
        onSubmit={() => void handleForkThread()}
        isSubmitting={forkThread.isPending}
      />

      <Dialog open={addContextOpen} onOpenChange={setAddContextOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>添加上下文卡片</DialogTitle>
            <DialogDescription>
              当前支持从基础来源和高级研究对象导入到当前线程，长期上下文只会在你显式导入时挂载。
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4">
            <div className="grid gap-3 md:grid-cols-2">
              <Select value={addContextSource} onValueChange={setAddContextSource}>
                <SelectTrigger>
                  <SelectValue placeholder="选择来源" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="tradingagents_run">TradingAgents</SelectItem>
                  <SelectItem value="holding">持仓</SelectItem>
                  <SelectItem value="opportunity">机会池</SelectItem>
                  <SelectItem value="watchlist">观察池</SelectItem>
                  <SelectItem value="theme">题材雷达</SelectItem>
                  <SelectItem value="alert">提醒</SelectItem>
                  <SelectItem value="decision_context_window">决策上下文</SelectItem>
                  <SelectItem value="decision_outcome_review">结果回看</SelectItem>
                  <SelectItem value="risk_sizing">分仓建议</SelectItem>
                  <SelectItem value="decision_effectiveness">有效性摘要</SelectItem>
                </SelectContent>
              </Select>
              <Select value={addContextMode} onValueChange={(value) => setAddContextMode(value as "append" | "replace")}>
                <SelectTrigger>
                  <SelectValue placeholder="选择导入模式" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="append">append</SelectItem>
                  <SelectItem value="replace">replace</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="max-h-[420px] space-y-3 overflow-y-auto rounded-xl border p-3">
              {contextSourceItems.length ? (
                contextSourceItems.map((item) => (
                  <div key={item.ref} className="rounded-xl border p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1">
                        <p className="font-medium text-sm">{item.title}</p>
                        <p className="text-muted-foreground text-xs">{item.subtitle}</p>
                        <p className="text-sm">{item.summary}</p>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleImportContext(addContextSource, item.ref)}
                        disabled={!currentThread || importContext.isPending}
                      >
                        {importContext.isPending ? "导入中..." : "加入线程"}
                      </Button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                  当前来源暂无可导入项。
                </div>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddContextOpen(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
