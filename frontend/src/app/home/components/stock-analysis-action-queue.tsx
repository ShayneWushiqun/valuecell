import { Link } from "react-router";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { StockAnalysisOverviewActionQueueItem } from "@/types/stock-analysis-overview";

type StockAnalysisActionQueueProps = {
  items: StockAnalysisOverviewActionQueueItem[];
};

export function StockAnalysisActionQueue({ items }: StockAnalysisActionQueueProps) {
  return (
    <div className="rounded-2xl border bg-background p-5">
      <p className="font-medium text-base">Action Queue</p>
      <p className="mt-1 text-muted-foreground text-sm">
        只做导航和建议，不自动执行 refresh、task 或 feedback。
      </p>
      <div className="mt-3 space-y-3">
        {items.length ? (
          items.map((item) => (
            <div
              key={`${item.kind}-${item.thread_id}-${item.target_ref || ""}`}
              className="rounded-xl border p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="secondary">{item.kind}</Badge>
                <Badge variant="outline">{item.priority}</Badge>
              </div>
              <p className="mt-3 font-medium text-sm">{item.title}</p>
              <p className="mt-1 text-muted-foreground text-sm">{item.summary}</p>
              <p className="mt-2 text-sm">原因：{item.reason}</p>
              <p className="mt-1 text-sm">建议动作：{item.suggested_action}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button asChild size="sm" variant="outline">
                  <Link to={`/home/stock-analysis?threadId=${item.thread_id}`}>
                    去线程处理
                  </Link>
                </Button>
                <Badge variant="outline">{item.target_ref || `thread:${item.thread_id}`}</Badge>
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-lg border border-dashed p-4 text-muted-foreground text-sm">
            当前没有需要优先处理的 action queue。
          </div>
        )}
      </div>
    </div>
  );
}
