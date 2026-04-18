import { Badge } from "@/components/ui/badge";
import type { StockAnalysisRefreshRunResult } from "@/types/analysis-context-card";

type StockAnalysisRefreshSummaryProps = {
  refreshRun?: StockAnalysisRefreshRunResult | null;
};

export function StockAnalysisRefreshSummary({
  refreshRun,
}: StockAnalysisRefreshSummaryProps) {
  if (!refreshRun) {
    return null;
  }

  return (
    <div className="rounded-xl border border-dashed p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary">最近刷新结果</Badge>
        <Badge variant="outline">刷新 {refreshRun.refreshed_count}</Badge>
        <Badge variant="outline">跳过 {refreshRun.skipped_count}</Badge>
        <Badge variant="outline">失败 {refreshRun.failed_count}</Badge>
      </div>
      <p className="mt-2">{refreshRun.summary}</p>
      {refreshRun.changed_contexts.length ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {refreshRun.changed_contexts.map((item) => (
            <Badge key={item.context_id} variant="outline" className="whitespace-normal">
              {item.title}: {item.changed_fields.join(", ") || "no material change"}
            </Badge>
          ))}
        </div>
      ) : null}
    </div>
  );
}
