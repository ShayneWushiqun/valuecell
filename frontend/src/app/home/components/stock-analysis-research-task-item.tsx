import { RotateCcw, Sparkles, CheckCircle2, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { StockAnalysisResearchTask } from "@/types/stock-analysis-research-task";

const formatTime = (value?: string | null) => {
  if (!value) return "暂无";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN");
};

type StockAnalysisResearchTaskItemProps = {
  task: StockAnalysisResearchTask;
  actionPending?: boolean;
  onComplete: (task: StockAnalysisResearchTask) => void;
  onReopen: (task: StockAnalysisResearchTask) => void;
  onDismiss: (task: StockAnalysisResearchTask) => void;
};

export function StockAnalysisResearchTaskItem({
  task,
  actionPending = false,
  onComplete,
  onReopen,
  onDismiss,
}: StockAnalysisResearchTaskItemProps) {
  return (
    <div className="rounded-xl border p-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={task.priority === "high" ? "secondary" : "outline"}>
          {task.priority}
        </Badge>
        <Badge variant="outline">{task.task_type}</Badge>
        <Badge variant="outline">{task.status}</Badge>
        <Badge variant="outline">{task.source_kind}</Badge>
      </div>
      <div className="mt-3 space-y-2">
        <p className="font-medium text-sm">{task.title}</p>
        <p className="text-muted-foreground text-sm">
          {task.summary || "当前没有补充摘要。"}
        </p>
        {task.related_tickers_json.length || task.related_themes_json.length ? (
          <div className="flex flex-wrap gap-2 text-xs">
            {task.related_tickers_json.map((ticker) => (
              <Badge key={ticker} variant="outline">
                {ticker}
              </Badge>
            ))}
            {task.related_themes_json.map((theme) => (
              <Badge key={theme} variant="outline">
                {theme}
              </Badge>
            ))}
          </div>
        ) : null}
        <p className="text-muted-foreground text-xs">
          更新时间：{formatTime(task.updated_at)}
        </p>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {task.status === "open" ? (
          <>
            <Button
              size="sm"
              variant="outline"
              disabled={actionPending}
              onClick={() => onComplete(task)}
            >
              <CheckCircle2 className="size-4" />
              完成
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={actionPending}
              onClick={() => onDismiss(task)}
            >
              <XCircle className="size-4" />
              忽略
            </Button>
          </>
        ) : (
          <Button
            size="sm"
            variant="outline"
            disabled={actionPending}
            onClick={() => onReopen(task)}
          >
            <RotateCcw className="size-4" />
            重开
          </Button>
        )}
        {task.source_kind === "assistant_suggestion" ? (
          <Badge variant="secondary" className="gap-1">
            <Sparkles className="size-3" />
            assistant suggestion
          </Badge>
        ) : null}
      </div>
    </div>
  );
}
