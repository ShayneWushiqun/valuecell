import { useMemo } from "react";
import { useGetOpportunityCandidates } from "@/api/opportunity-pool";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";

const formatPercent = (value?: number | null) => {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
};

const getCandidateStateClassName = (candidateState: string) => {
  if (candidateState.includes("高优先级")) return "bg-emerald-500/10 text-emerald-500";
  if (candidateState.includes("候选")) return "bg-blue-500/10 text-blue-500";
  if (candidateState.includes("暂不参与")) return "bg-red-500/10 text-red-500";
  if (candidateState.includes("仅适合持有")) return "bg-orange-500/10 text-orange-500";
  return "bg-muted text-muted-foreground";
};

const getRankingBucketClassName = (bucket: string) => {
  if (bucket === "A") return "bg-emerald-500/10 text-emerald-500";
  if (bucket === "B") return "bg-blue-500/10 text-blue-500";
  return "bg-muted text-muted-foreground";
};

export default function OpportunityPoolPanel() {
  const {
    data: opportunityPool,
    isLoading,
    isError,
  } = useGetOpportunityCandidates();

  const visibleItems = useMemo(
    () => (opportunityPool?.items || []).slice(0, 4),
    [opportunityPool?.items],
  );

  return (
    <div className="rounded-3xl border bg-card p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold text-lg">候选机会</h2>
          <p className="mt-1 text-muted-foreground text-sm">
            先看候选机会和等待确认项，不直接给出绝对买入判断。
          </p>
        </div>
        {opportunityPool?.source_summary ? (
          <div className="flex flex-wrap justify-end gap-2">
            <Badge variant="secondary">
              候选 {opportunityPool.source_summary.candidate_count}
            </Badge>
            <Badge variant="outline">
              自选 {opportunityPool.source_summary.watchlist_count}
            </Badge>
            <Badge variant="outline">
              题材 {opportunityPool.source_summary.theme_candidate_count}
            </Badge>
          </div>
        ) : null}
      </div>

      {isLoading ? (
        <div className="flex min-h-40 items-center justify-center">
          <Spinner className="size-5" />
        </div>
      ) : null}

      {!isLoading && (isError || !opportunityPool?.available || !visibleItems.length) ? (
        <div className="mt-4 rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
          {opportunityPool?.empty_message || "暂无可用机会池候选"}
        </div>
      ) : null}

      {!isLoading && !isError && visibleItems.length ? (
        <div className="mt-4 grid gap-3 xl:grid-cols-2">
          {visibleItems.map((item) => (
            <div key={item.ticker} className="rounded-2xl border bg-background p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium text-sm">{item.display_name}</p>
                    <Badge className={getCandidateStateClassName(item.candidate_state)}>
                      {item.candidate_state}
                    </Badge>
                    <Badge className={getRankingBucketClassName(item.ranking_bucket)}>
                      {item.ranking_bucket}
                    </Badge>
                  </div>
                  <p className="truncate text-muted-foreground text-xs">
                    {item.ticker}
                    {item.topic_name ? ` · ${item.topic_name}` : ""}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-medium text-sm">{item.latest_price || "--"}</p>
                  <p
                    className={`text-xs ${
                      (item.change_percent || 0) >= 0
                        ? "text-emerald-500"
                        : "text-red-500"
                    }`}
                  >
                    {formatPercent(item.change_percent)}
                  </p>
                </div>
              </div>

              <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                <span>优先分 {item.priority_score}</span>
                <span>· {item.role_label}</span>
                <span>· {item.trend_quality}</span>
                <span>· 预期差 {item.expectation_gap_level}</span>
                <span>· {item.tradeability_state}</span>
              </div>

              <div className="mt-3 space-y-1 text-sm">
                {item.reasons.slice(0, 2).map((reason) => (
                  <p key={reason}>- {reason}</p>
                ))}
              </div>

              <div className="mt-3 rounded-xl bg-muted/50 p-3 text-sm">
                <p className="font-medium text-xs text-muted-foreground">行动提示</p>
                <p className="mt-1">{item.action_hint}</p>
              </div>

              {item.invalid_conditions.length ? (
                <div className="mt-3 rounded-xl border border-red-500/20 bg-red-500/5 p-3 text-sm">
                  <p className="font-medium text-red-500 text-xs">风险条件 / 暂不参与</p>
                  <div className="mt-1 space-y-1">
                    {item.invalid_conditions.map((condition) => (
                      <p key={condition}>- {condition}</p>
                    ))}
                  </div>
                </div>
              ) : null}

              {item.missing_confirmations.length ? (
                <div className="mt-3 rounded-xl border border-orange-500/20 bg-orange-500/5 p-3 text-sm">
                  <p className="font-medium text-orange-500 text-xs">还需确认</p>
                  <div className="mt-1 space-y-1">
                    {item.missing_confirmations.slice(0, 2).map((confirmation) => (
                      <p key={confirmation}>- {confirmation}</p>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
