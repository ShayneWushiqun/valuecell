import { Link } from "react-router";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { StockAnalysisThreadOverviewItem } from "@/types/stock-analysis-overview";

type StockAnalysisThreadOverviewCardProps = {
  item: StockAnalysisThreadOverviewItem;
};

export function StockAnalysisThreadOverviewCard({
  item,
}: StockAnalysisThreadOverviewCardProps) {
  return (
    <div className="rounded-2xl border bg-background p-5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary">{item.thread_health_status}</Badge>
        <Badge variant="outline">score {item.thread_health_score}</Badge>
        {item.latest_planning_profile ? (
          <Badge variant="outline">{item.latest_planning_profile}</Badge>
        ) : null}
        {item.latest_conflict_level ? (
          <Badge variant="outline">conflict {item.latest_conflict_level}</Badge>
        ) : null}
        {item.latest_feedback_alignment_status ? (
          <Badge variant="outline">{item.latest_feedback_alignment_status}</Badge>
        ) : null}
      </div>
      <div className="mt-3 flex items-start justify-between gap-3">
        <div>
          <p className="font-medium text-sm">{item.title}</p>
          <p className="mt-1 text-muted-foreground text-sm">{item.headline_summary}</p>
        </div>
        <Badge variant="outline">{item.focus_type}</Badge>
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        <Badge variant="outline">context {item.context_count}</Badge>
        <Badge variant="outline">compare {item.compare_target_count}</Badge>
        <Badge variant="outline">open tasks {item.open_task_count}</Badge>
        <Badge variant="outline">high priority {item.high_priority_task_count}</Badge>
        <Badge variant="outline">stale {item.stale_context_count}</Badge>
        <Badge variant="outline">refresh {item.refresh_recommended_count}</Badge>
      </div>
      <p className="mt-3 text-sm">Next Best Action：{item.next_best_action}</p>
      <p className="mt-1 text-muted-foreground text-sm">{item.next_best_action_reason}</p>
      <p className="mt-2 text-muted-foreground text-xs">{item.thread_health_reason}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button asChild size="sm" variant="outline">
          <Link to={`/home/stock-analysis?threadId=${item.thread_id}`}>查看线程</Link>
        </Button>
        <Badge variant="outline">
          {item.active_memory_available ? "memory on" : "memory off"}
        </Badge>
        <Badge variant="outline">
          {item.active_compression_available ? "compression on" : "compression off"}
        </Badge>
      </div>
    </div>
  );
}
