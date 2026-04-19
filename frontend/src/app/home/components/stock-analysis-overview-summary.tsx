import { Badge } from "@/components/ui/badge";
import type { StockAnalysisOverview } from "@/types/stock-analysis-overview";

type StockAnalysisOverviewSummaryProps = {
  overview: StockAnalysisOverview;
};

export function StockAnalysisOverviewSummary({
  overview,
}: StockAnalysisOverviewSummaryProps) {
  return (
    <div className="rounded-2xl border bg-background p-5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary">V1.5 Global Overview</Badge>
        <Badge variant="outline">
          最近反馈 {overview.recent_feedback_summary.total_feedback_count}
        </Badge>
      </div>
      <p className="mt-3 font-medium text-base">当前研究系统最值得先看的线程与动作</p>
      <p className="mt-2 text-muted-foreground text-sm">{overview.summary}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <Badge variant="secondary">线程 {overview.thread_overview_items.length}</Badge>
        <Badge variant="outline">Action Queue {overview.action_queue.length}</Badge>
        <Badge variant="outline">高冲突 {overview.high_conflict_threads.length}</Badge>
        <Badge variant="outline">需 Refresh {overview.refresh_needed_threads.length}</Badge>
        <Badge variant="outline">高优任务 {overview.high_priority_tasks.length}</Badge>
        <Badge variant="outline">
          有效线程 {overview.recent_feedback_summary.effective_thread_count}
        </Badge>
      </div>
    </div>
  );
}
