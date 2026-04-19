import { useMemo, useState } from "react";
import { History, ListTodo, Plus, Sparkles } from "lucide-react";
import { StockAnalysisResearchTaskList } from "@/app/home/components/stock-analysis-research-task-list";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
  StockAnalysisResearchTask,
  StockAnalysisResearchTaskList as StockAnalysisResearchTaskListData,
} from "@/types/stock-analysis-research-task";

type ManualTaskDraft = {
  title: string;
  summary: string;
  task_type: StockAnalysisResearchTask["task_type"];
  priority: StockAnalysisResearchTask["priority"];
  relatedTickers: string;
  relatedThemes: string;
};

const EMPTY_DRAFT: ManualTaskDraft = {
  title: "",
  summary: "",
  task_type: "next_question",
  priority: "medium",
  relatedTickers: "",
  relatedThemes: "",
};

const splitRefs = (value: string) =>
  value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

const formatTime = (value?: string | null) => {
  if (!value) return "暂无";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN");
};

type StockAnalysisResearchTaskPanelProps = {
  taskData: StockAnalysisResearchTaskListData | null | undefined;
  currentFocusTickers?: string[];
  currentFocusThemes?: string[];
  relatedTaskIds?: number[];
  isLoading?: boolean;
  generatePending?: boolean;
  createPending?: boolean;
  actionPending?: boolean;
  onGenerate: () => void;
  onCreate: (draft: {
    title: string;
    summary: string;
    task_type: StockAnalysisResearchTask["task_type"];
    priority: StockAnalysisResearchTask["priority"];
    related_tickers_json: string[];
    related_themes_json: string[];
  }) => void;
  onResearch: (task: StockAnalysisResearchTask) => void;
  onComplete: (task: StockAnalysisResearchTask) => void;
  onReopen: (task: StockAnalysisResearchTask) => void;
  onDismiss: (task: StockAnalysisResearchTask) => void;
};

export function StockAnalysisResearchTaskPanel({
  taskData,
  currentFocusTickers = [],
  currentFocusThemes = [],
  relatedTaskIds = [],
  isLoading = false,
  generatePending = false,
  createPending = false,
  actionPending = false,
  onGenerate,
  onCreate,
  onResearch,
  onComplete,
  onReopen,
  onDismiss,
}: StockAnalysisResearchTaskPanelProps) {
  const [showHistory, setShowHistory] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [draft, setDraft] = useState<ManualTaskDraft>(EMPTY_DRAFT);

  const enhanceTask = (item: StockAnalysisResearchTask): StockAnalysisResearchTask => ({
    ...item,
    is_focus_related:
      item.related_tickers_json.some((ticker) => currentFocusTickers.includes(ticker)) ||
      item.related_themes_json.some((theme) => currentFocusThemes.includes(theme)),
    is_related_to_latest_message: relatedTaskIds.includes(item.task_id),
  });

  const openTasks = useMemo(
    () =>
      (taskData?.items || [])
        .filter((item) => item.status === "open")
        .map((item) => enhanceTask(item)),
    [taskData, currentFocusTickers, currentFocusThemes, relatedTaskIds],
  );
  const historyTasks = useMemo(
    () =>
      (taskData?.items || [])
        .filter((item) => item.status !== "open")
        .map((item) => enhanceTask(item)),
    [taskData, currentFocusTickers, currentFocusThemes, relatedTaskIds],
  );

  const submitCreate = () => {
    if (!draft.title.trim()) return;
    onCreate({
      title: draft.title.trim(),
      summary: draft.summary.trim(),
      task_type: draft.task_type,
      priority: draft.priority,
      related_tickers_json: splitRefs(draft.relatedTickers),
      related_themes_json: splitRefs(draft.relatedThemes),
    });
    setDraft(EMPTY_DRAFT);
    setShowCreateForm(false);
  };

  return (
    <div className="rounded-xl border p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-medium text-sm">Research Tasks</p>
          <p className="text-muted-foreground text-xs">
            把 compare / refresh / memory / compression / assistant suggestion
            显式沉淀成可跟踪研究清单。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={onGenerate} disabled={generatePending}>
            <Sparkles className="size-4" />
            {generatePending ? "生成中..." : "生成研究任务"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowCreateForm((value) => !value)}
          >
            <Plus className="size-4" />
            {showCreateForm ? "收起手动任务" : "新建手动任务"}
          </Button>
          <Button size="sm" variant="outline" onClick={() => setShowHistory((value) => !value)}>
            <History className="size-4" />
            {showHistory ? "收起历史" : "查看历史任务"}
          </Button>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        <Badge variant="secondary">Open {taskData?.open_count || 0}</Badge>
        <Badge variant="outline">High {taskData?.high_priority_open_count || 0}</Badge>
        <Badge variant="outline">当前相关 {relatedTaskIds.length}</Badge>
        <Badge variant={taskData?.has_actionable_gap ? "secondary" : "outline"}>
          {taskData?.has_actionable_gap ? "存在立即处理 gap" : "当前 gap 可控"}
        </Badge>
        <Badge variant="outline">
          最近 generate：{formatTime(taskData?.last_generated_at)}
        </Badge>
      </div>
      <p className="mt-2 text-muted-foreground text-xs">
        {taskData?.actionable_gap_summary || "当前线程还没有显式 research tasks。"}
      </p>

      <div className="mt-4 space-y-3">
        {showCreateForm ? (
          <div className="space-y-3 rounded-xl border border-dashed p-4">
            <div className="grid gap-3 md:grid-cols-2">
              <Input
                value={draft.title}
                onChange={(event) =>
                  setDraft((current) => ({ ...current, title: event.target.value }))
                }
                placeholder="任务标题，例如：刷新后重看当前结论"
              />
              <div className="grid grid-cols-2 gap-3">
                <Select
                  value={draft.task_type}
                  onValueChange={(value) =>
                    setDraft((current) => ({
                      ...current,
                      task_type: value as StockAnalysisResearchTask["task_type"],
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="任务类型" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="next_question">next_question</SelectItem>
                    <SelectItem value="compare_followup">compare_followup</SelectItem>
                    <SelectItem value="refresh_needed">refresh_needed</SelectItem>
                    <SelectItem value="tooling_check">tooling_check</SelectItem>
                    <SelectItem value="memory_recheck">memory_recheck</SelectItem>
                    <SelectItem value="compression_recheck">compression_recheck</SelectItem>
                    <SelectItem value="risk_recheck">risk_recheck</SelectItem>
                    <SelectItem value="thesis_validation">thesis_validation</SelectItem>
                  </SelectContent>
                </Select>
                <Select
                  value={draft.priority}
                  onValueChange={(value) =>
                    setDraft((current) => ({
                      ...current,
                      priority: value as StockAnalysisResearchTask["priority"],
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="优先级" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="high">high</SelectItem>
                    <SelectItem value="medium">medium</SelectItem>
                    <SelectItem value="low">low</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Textarea
              value={draft.summary}
              onChange={(event) =>
                setDraft((current) => ({ ...current, summary: event.target.value }))
              }
              placeholder="任务摘要，例如：当前结论依赖旧上下文，建议 refresh 后再验证。"
            />
            <div className="grid gap-3 md:grid-cols-2">
              <Input
                value={draft.relatedTickers}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,
                    relatedTickers: event.target.value,
                  }))
                }
                placeholder="相关 ticker，逗号分隔"
              />
              <Input
                value={draft.relatedThemes}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,
                    relatedThemes: event.target.value,
                  }))
                }
                placeholder="相关 theme，逗号分隔"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setDraft(EMPTY_DRAFT);
                  setShowCreateForm(false);
                }}
              >
                取消
              </Button>
              <Button size="sm" onClick={submitCreate} disabled={createPending}>
                {createPending ? "创建中..." : "保存任务"}
              </Button>
            </div>
          </div>
        ) : null}

        {isLoading ? (
          <div className="flex min-h-24 items-center justify-center rounded-xl border border-dashed">
            <Spinner className="size-5" />
          </div>
        ) : (
          <StockAnalysisResearchTaskList
            tasks={openTasks}
            emptyText="当前没有 open research tasks。可以从线程生成，或手动创建下一步研究任务。"
            actionPending={actionPending}
            onResearch={onResearch}
            onComplete={onComplete}
            onReopen={onReopen}
            onDismiss={onDismiss}
          />
        )}

        {showHistory ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm">
              <ListTodo className="size-4" />
              <p className="font-medium">历史任务</p>
            </div>
            <StockAnalysisResearchTaskList
              tasks={historyTasks}
              emptyText="当前没有 completed / dismissed 的历史任务。"
              actionPending={actionPending}
              onResearch={onResearch}
              onComplete={onComplete}
              onReopen={onReopen}
              onDismiss={onDismiss}
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}
