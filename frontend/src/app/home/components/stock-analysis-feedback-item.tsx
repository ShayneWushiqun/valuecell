import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { StockAnalysisResearchFeedback } from "@/types/stock-analysis-research-feedback";

const formatTime = (value?: string | null) => {
  if (!value) return "暂无";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN");
};

type StockAnalysisFeedbackItemProps = {
  feedback: StockAnalysisResearchFeedback;
  selected?: boolean;
  refreshPending?: boolean;
  onRefresh?: (feedbackId: number) => void;
};

export function StockAnalysisFeedbackItem({
  feedback,
  selected = false,
  refreshPending = false,
  onRefresh,
}: StockAnalysisFeedbackItemProps) {
  return (
    <div
      className={`rounded-xl border p-3 ${
        selected ? "border-primary bg-accent/30" : ""
      }`}
    >
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary">v{feedback.version}</Badge>
        <Badge variant="outline">{feedback.outcome_alignment_status}</Badge>
        <Badge variant="outline">{feedback.process_quality_status}</Badge>
        {feedback.compare_helpful ? <Badge variant="outline">compare 有帮助</Badge> : null}
        {feedback.refresh_helpful ? <Badge variant="outline">refresh 有帮助</Badge> : null}
        {feedback.tooling_helpful ? <Badge variant="outline">tooling 有帮助</Badge> : null}
        {feedback.validation_helpful ? <Badge variant="outline">validation 有帮助</Badge> : null}
      </div>
      <div className="mt-3 space-y-2">
        <p className="font-medium text-sm">{feedback.title}</p>
        <p className="text-muted-foreground text-sm">{feedback.summary}</p>
        {feedback.linked_tickers_json.length || feedback.linked_task_ids_json.length ? (
          <div className="flex flex-wrap gap-2 text-xs">
            {feedback.linked_tickers_json.map((ticker) => (
              <Badge key={ticker} variant="outline">
                {ticker}
              </Badge>
            ))}
            {feedback.linked_task_ids_json.map((taskId) => (
              <Badge key={`task-${taskId}`} variant="outline">
                task #{taskId}
              </Badge>
            ))}
          </div>
        ) : null}
        {feedback.what_helped_json.length ? (
          <p className="text-sm">
            <span className="font-medium">helped:</span> {feedback.what_helped_json.join("；")}
          </p>
        ) : null}
        {feedback.what_hurt_json.length ? (
          <p className="text-sm">
            <span className="font-medium">hurt:</span> {feedback.what_hurt_json.join("；")}
          </p>
        ) : null}
        {feedback.process_adjustments_json.length ? (
          <p className="text-sm">
            <span className="font-medium">process adjustments:</span>{" "}
            {feedback.process_adjustments_json.join("；")}
          </p>
        ) : null}
        {feedback.task_followup_suggestions_json.length ? (
          <div className="space-y-1 text-sm">
            <p className="font-medium">task follow-up suggestions</p>
            {feedback.task_followup_suggestions_json.map((item) => (
              <div key={`${feedback.feedback_id}-${item.task_id}`} className="rounded border p-2">
                <p>
                  #{item.task_id} {item.title} · {item.suggestion}
                </p>
                <p className="text-muted-foreground text-xs">{item.reason}</p>
              </div>
            ))}
          </div>
        ) : null}
        {feedback.detail_note ? (
          <p className="whitespace-pre-wrap text-muted-foreground text-xs">
            {feedback.detail_note}
          </p>
        ) : null}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-muted-foreground text-xs">
            更新于 {formatTime(feedback.updated_at)} · anchor {feedback.anchor_message_id}
          </p>
          {onRefresh ? (
            <Button
              size="sm"
              variant="outline"
              disabled={refreshPending}
              onClick={() => onRefresh(feedback.feedback_id)}
            >
              {refreshPending ? "刷新中..." : "刷新研究反馈"}
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
