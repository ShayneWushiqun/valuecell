import BackButton from "@valuecell/button/back-button";
import { Copy, Pin, PinOff, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { toast } from "sonner";
import {
  useCreateStockAnalysisThread,
  useDeleteStockAnalysisContext,
  useDeleteStockAnalysisThread,
  useDuplicateStockAnalysisThread,
  useGetStockAnalysisContexts,
  useGetStockAnalysisWorkspaceOverview,
  useUpdateStockAnalysisContext,
  useUpdateStockAnalysisThread,
} from "@/api/stock-analysis";
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
  const [newTitle, setNewTitle] = useState("");
  const [newFocusType, setNewFocusType] = useState<string>("mixed");
  const [newTickerRefs, setNewTickerRefs] = useState("");
  const [newThemeRefs, setNewThemeRefs] = useState("");
  const [renameOpen, setRenameOpen] = useState(false);
  const [renameTitle, setRenameTitle] = useState("");
  const [editingThread, setEditingThread] = useState<StockAnalysisThread | null>(null);

  const { data: overview, isLoading, isError } =
    useGetStockAnalysisWorkspaceOverview(selectedThreadId);
  const { data: contexts, isLoading: contextsLoading } =
    useGetStockAnalysisContexts(selectedThreadId);
  const createThread = useCreateStockAnalysisThread();
  const updateThread = useUpdateStockAnalysisThread();
  const deleteThread = useDeleteStockAnalysisThread();
  const duplicateThread = useDuplicateStockAnalysisThread();
  const updateContext = useUpdateStockAnalysisContext();
  const deleteContext = useDeleteStockAnalysisContext();

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

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-semibold text-2xl">股票分析工作区</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            本轮先完成线程式研究骨架、上下文管理和 TradingAgents 导入，不接真正聊天执行。
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
              <CardDescription>本轮只完成 conversation 绑定和研究骨架，下一轮再接真正聊天执行。</CardDescription>
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
                    <p className="font-medium text-sm">conversation_id</p>
                    <p className="mt-2 break-all font-mono text-muted-foreground text-sm">
                      {currentThread.conversation_id}
                    </p>
                    <p className="mt-3 text-muted-foreground text-sm">
                      当前还未启用真正问答和 stream。本轮只把线程、上下文卡片和会话绑定先打稳。
                    </p>
                  </div>

                  <div className="flex min-h-0 flex-1 flex-col rounded-xl border p-4">
                    <p className="font-medium text-sm">聊天区占位</p>
                    <div className="mt-3 flex min-h-0 flex-1 flex-col gap-3">
                      <div className="flex-1 rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                        下一轮会把真正的 stock-analysis message stream 接到这里。本轮先保留线程式研究工作区骨架。
                      </div>
                      <Textarea
                        disabled
                        value="本轮输入区仅作占位，尚未启用真正发送。"
                        className="min-h-24"
                      />
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
              <CardTitle>上下文卡片</CardTitle>
              <CardDescription>本轮只接 TradingAgents run 导入，其它模块导入留到下一轮。</CardDescription>
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
                    </div>
                    {item.staleness_hint ? (
                      <p className="mt-3 text-muted-foreground text-xs">{item.staleness_hint}</p>
                    ) : null}
                  </div>
                ))
              ) : (
                <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                  当前线程还没有上下文卡片。可先去 TradingAgents 选择一个 run 导入到这里。
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
    </div>
  );
}
