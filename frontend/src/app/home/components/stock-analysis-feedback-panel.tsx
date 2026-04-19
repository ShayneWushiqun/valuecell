import { useMemo, useState } from "react";
import { History, Sparkles } from "lucide-react";
import { StockAnalysisFeedbackList } from "@/app/home/components/stock-analysis-feedback-list";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import type {
  StockAnalysisResearchFeedback,
  StockAnalysisResearchFeedbackList,
} from "@/types/stock-analysis-research-feedback";

type StockAnalysisFeedbackPanelProps = {
  feedbackData: StockAnalysisResearchFeedbackList | null | undefined;
  isLoading?: boolean;
  capturePending?: boolean;
  refreshPending?: boolean;
  selectedFeedbackId?: number | null;
  onCaptureLatest: () => void;
  onRefresh: (feedbackId: number) => void;
};

export function StockAnalysisFeedbackPanel({
  feedbackData,
  isLoading = false,
  capturePending = false,
  refreshPending = false,
  selectedFeedbackId,
  onCaptureLatest,
  onRefresh,
}: StockAnalysisFeedbackPanelProps) {
  const [showHistory, setShowHistory] = useState(false);

  const latestFeedback = feedbackData?.latest_feedback || null;
  const historyItems = useMemo(
    () =>
      (feedbackData?.items || []).filter(
        (item) => item.feedback_id !== latestFeedback?.feedback_id,
      ),
    [feedbackData?.items, latestFeedback?.feedback_id],
  );
  const trackingSuggestionCount = useMemo(
    () =>
      (feedbackData?.items || []).reduce((count, item) => {
        return (
          count +
          item.task_followup_suggestions_json.filter((task) =>
            ["keep_tracking", "convert_to_refresh_check", "reopen_for_research"].includes(
              task.suggestion,
            ),
          ).length
        );
      }, 0),
    [feedbackData?.items],
  );

  return (
    <div className="rounded-xl border p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-medium text-sm">Research Feedback</p>
          <p className="text-muted-foreground text-xs">
            回看某轮研究后来是否被结果支持，并沉淀这条线程里更有效的研究方式。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={onCaptureLatest}
            disabled={capturePending}
          >
            <Sparkles className="size-4" />
            {capturePending ? "生成中..." : "生成研究反馈"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowHistory((value) => !value)}
          >
            <History className="size-4" />
            {showHistory ? "收起历史" : "查看反馈历史"}
          </Button>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        <Badge variant="secondary">recent feedback {feedbackData?.count || 0}</Badge>
        <Badge variant="outline">
          跟踪建议 {trackingSuggestionCount}
        </Badge>
        {latestFeedback ? (
          <>
            <Badge variant="outline">{latestFeedback.outcome_alignment_status}</Badge>
            <Badge variant="outline">{latestFeedback.process_quality_status}</Badge>
          </>
        ) : null}
      </div>
      <div className="mt-4 space-y-3">
        {isLoading ? (
          <div className="flex min-h-24 items-center justify-center rounded-xl border border-dashed">
            <Spinner className="size-5" />
          </div>
        ) : latestFeedback ? (
          <StockAnalysisFeedbackList
            feedbackItems={[latestFeedback]}
            emptyText=""
            selectedFeedbackId={selectedFeedbackId}
            refreshPending={refreshPending}
            onRefresh={onRefresh}
          />
        ) : (
          <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
            当前线程还没有研究反馈。可以先从最近一轮 assistant 研究消息生成第一份反馈快照。
          </div>
        )}
        {showHistory ? (
          <StockAnalysisFeedbackList
            feedbackItems={historyItems as StockAnalysisResearchFeedback[]}
            emptyText="当前还没有更多历史 feedback。"
            selectedFeedbackId={selectedFeedbackId}
            refreshPending={refreshPending}
            onRefresh={onRefresh}
          />
        ) : null}
      </div>
    </div>
  );
}
