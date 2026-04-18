import BackButton from "@valuecell/button/back-button";
import { Copy, Pin, PinOff, Plus, Send, Trash2 } from "lucide-react";
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
  useCreateStockAnalysisMessage,
  useCreateStockAnalysisThread,
  useDeleteStockAnalysisContext,
  useDeleteStockAnalysisThread,
  useDuplicateStockAnalysisThread,
  useGetStockAnalysisContexts,
  useGetStockAnalysisMessages,
  useGetStockAnalysisWorkspaceOverview,
  useImportStockAnalysisContext,
  useUpdateStockAnalysisContext,
  useUpdateStockAnalysisThread,
} from "@/api/stock-analysis";
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
import type { StockAnalysisThread } from "@/types/stock-analysis-thread";

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
  const [editingThread, setEditingThread] = useState<StockAnalysisThread | null>(null);
  const autoImportKeyRef = useRef<string | null>(null);

  const { data: overview, isLoading, isError } =
    useGetStockAnalysisWorkspaceOverview(selectedThreadId);
  const { data: contexts, isLoading: contextsLoading } =
    useGetStockAnalysisContexts(selectedThreadId);
  const { data: messages, isLoading: messagesLoading } =
    useGetStockAnalysisMessages(selectedThreadId);
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
  const importContext = useImportStockAnalysisContext();
  const createMessage = useCreateStockAnalysisMessage();

  const threads = overview?.threads || [];
  const currentThread = useMemo(() => {
    if (!selectedThreadId) return overview?.current_thread || null;
    return threads.find((item) => item.thread_id === selectedThreadId) || null;
  }, [overview?.current_thread, selectedThreadId, threads]);

  useEffect(() => {
    if (!selectedThreadId && overview?.current_thread?.thread_id) {
      setSearchParams({ threadId: String(overview.current_thread.thread_id) });
    }
  }, [overview?.current_thread?.thread_id, selectedThreadId, setSearchParams]);

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

  const handleSendMessage = async (forceTooling = false) => {
    if (!currentThread) {
      toast.error("请先选中线程");
      return;
    }
    if (!messageInput.trim()) {
      toast.error("请输入研究问题");
      return;
    }
    try {
      await createMessage.mutateAsync({
        threadId: currentThread.thread_id,
        data: { message: messageInput.trim(), force_tooling: forceTooling },
      });
      setMessageInput("");
    } catch {
      toast.error("发送消息失败");
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
                        <Badge key={item} variant="outline">
                          {item}
                        </Badge>
                      ))}
                      {currentThread.theme_refs_json.map((item) => (
                        <Badge key={item} variant="outline">
                          {item}
                        </Badge>
                      ))}
                    </div>
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
                                item.role === "assistant" || item.role === "agent"
                                  ? "bg-primary/5"
                                  : "bg-background"
                              }`}
                            >
                              <div className="flex flex-wrap items-center gap-2">
                                <Badge variant="outline">
                                  {item.role === "assistant" || item.role === "agent"
                                    ? "研究助手"
                                    : "用户"}
                                </Badge>
                                {item.role === "assistant" || item.role === "agent" ? (
                                  <>
                                    <Badge variant="secondary">{item.answer_basis}</Badge>
                                    <Badge variant="outline">模式：{item.mode}</Badge>
                                    <Badge variant="outline">
                                      使用上下文 {item.used_context_ids.length} 张
                                    </Badge>
                                  </>
                                ) : null}
                              </div>
                              <p className="mt-3 whitespace-pre-wrap text-sm">{item.content}</p>
                              {item.role === "assistant" || item.role === "agent" ? (
                                <div className="mt-3 space-y-3">
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
                                              {item.temporary_evidence_blocks.map((block) => (
                                                <div
                                                  key={`${block.title}-${block.summary}`}
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
                                                  </div>
                                                  <p className="mt-1">{block.summary}</p>
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
                            正在基于当前上下文生成回答...
                          </div>
                        ) : null}
                      </div>
                      <Textarea
                        value={messageInput}
                        onChange={(event) => setMessageInput(event.target.value)}
                        placeholder="例如：先比较当前线程里这几只票的优先级；如果需要最新状态，再点“补数据后再回答”。"
                        className="min-h-24"
                      />
                      <p className="text-muted-foreground text-xs">
                        默认先基于当前上下文回答；若你明确需要最新价格、市场、题材或风险补充，可使用“补数据后再回答”。
                      </p>
                      <div className="flex flex-wrap justify-end gap-2">
                        <Button
                          variant="outline"
                          onClick={() => handleSendMessage(true)}
                          disabled={createMessage.isPending}
                        >
                          {createMessage.isPending ? "补数中..." : "补数据后再回答"}
                        </Button>
                        <Button
                          onClick={() => handleSendMessage(false)}
                          disabled={createMessage.isPending}
                        >
                          <Send className="size-4" />
                          {createMessage.isPending ? "生成中..." : "发送"}
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
              ) : contexts?.items.length ? (
                contexts.items.map((item) => (
                  <div key={item.context_id} className="rounded-xl border p-4">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant="secondary">{item.context_type}</Badge>
                        {item.is_pinned ? <Badge variant="outline">Pinned</Badge> : null}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="icon"
                          variant="outline"
                          onClick={() => handleTogglePin(item.context_id, item.is_pinned)}
                        >
                          {item.is_pinned ? (
                            <PinOff className="size-4" />
                          ) : (
                            <Pin className="size-4" />
                          )}
                        </Button>
                        <Button
                          size="icon"
                          variant="outline"
                          onClick={() => handleDeleteContext(item.context_id)}
                        >
                          <Trash2 className="size-4" />
                        </Button>
                      </div>
                    </div>
                    <p className="mt-3 font-medium text-sm">{item.title}</p>
                    {item.subtitle ? (
                      <p className="mt-1 text-muted-foreground text-xs">{item.subtitle}</p>
                    ) : null}
                    <p className="mt-3 text-sm">{item.summary}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {item.ticker_refs_json.map((ref) => (
                        <Badge key={ref} variant="outline">
                          {ref}
                        </Badge>
                      ))}
                      {item.theme_refs_json.map((ref) => (
                        <Badge key={ref} variant="outline">
                          {ref}
                        </Badge>
                      ))}
                    </div>
                    {item.staleness_hint ? (
                      <p className="mt-3 text-muted-foreground text-xs">{item.staleness_hint}</p>
                    ) : null}
                  </div>
                ))
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
