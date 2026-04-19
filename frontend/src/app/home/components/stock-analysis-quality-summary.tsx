import { Badge } from "@/components/ui/badge";
import type { StockAnalysisOverview } from "@/types/stock-analysis-overview";

type StockAnalysisQualitySummaryProps = {
  overview: StockAnalysisOverview;
};

export function StockAnalysisQualitySummary({
  overview,
}: StockAnalysisQualitySummaryProps) {
  const quality = overview.research_quality_summary;
  const planning = overview.planning_profile_summary;

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <div className="rounded-2xl border bg-background p-5">
        <p className="font-medium text-base">Research Quality</p>
        <p className="mt-1 text-muted-foreground text-sm">
          直接汇总最近 feedback 的过程质量与 outcome alignment。
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Badge variant="secondary">effective {quality.effective_count}</Badge>
          <Badge variant="outline">mixed {quality.mixed_count}</Badge>
          <Badge variant="outline">
            under-evidenced {quality.under_evidenced_count}
          </Badge>
          <Badge variant="outline">
            over-researched {quality.over_researched_count}
          </Badge>
          <Badge variant="outline">confirmed {quality.confirmed_count}</Badge>
          <Badge variant="outline">
            partially-confirmed {quality.partially_confirmed_count}
          </Badge>
          <Badge variant="outline">unclear {quality.unclear_count}</Badge>
          <Badge variant="outline">contradicted {quality.contradicted_count}</Badge>
        </div>
      </div>

      <div className="rounded-2xl border bg-background p-5">
        <p className="font-medium text-base">Planning Profiles</p>
        <p className="mt-1 text-muted-foreground text-sm">
          用来判断当前系统最近更偏哪种研究路径。
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Badge variant="secondary">balanced {planning.balanced_count}</Badge>
          <Badge variant="outline">
            refresh-first {planning.refresh_first_count}
          </Badge>
          <Badge variant="outline">
            compare-first {planning.compare_first_count}
          </Badge>
          <Badge variant="outline">
            internal-first {planning.internal_first_count}
          </Badge>
          <Badge variant="outline">
            external-confirm {planning.external_confirm_first_count}
          </Badge>
          <Badge variant="outline">
            lightweight {planning.lightweight_research_count}
          </Badge>
        </div>
      </div>
    </div>
  );
}
