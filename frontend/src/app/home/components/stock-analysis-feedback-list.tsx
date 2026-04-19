import { StockAnalysisFeedbackItem } from "@/app/home/components/stock-analysis-feedback-item";
import type { StockAnalysisResearchFeedback } from "@/types/stock-analysis-research-feedback";

type StockAnalysisFeedbackListProps = {
  feedbackItems: StockAnalysisResearchFeedback[];
  emptyText: string;
  selectedFeedbackId?: number | null;
  refreshPending?: boolean;
  onRefresh?: (feedbackId: number) => void;
};

export function StockAnalysisFeedbackList({
  feedbackItems,
  emptyText,
  selectedFeedbackId,
  refreshPending = false,
  onRefresh,
}: StockAnalysisFeedbackListProps) {
  if (!feedbackItems.length) {
    return (
      <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
        {emptyText}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {feedbackItems.map((feedback) => (
        <StockAnalysisFeedbackItem
          key={feedback.feedback_id}
          feedback={feedback}
          selected={selectedFeedbackId === feedback.feedback_id}
          refreshPending={refreshPending}
          onRefresh={onRefresh}
        />
      ))}
    </div>
  );
}
