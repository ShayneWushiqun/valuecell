import { useMemo } from "react";
import { Link } from "react-router";
import { useGetOpportunityCandidates } from "@/api/opportunity-pool";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import OpportunityCandidateCard from "./opportunity-candidate-card";

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
        <div className="flex flex-col items-end gap-2">
          <Button asChild size="sm" variant="outline">
            <Link to="/home/opportunities">查看全部机会池</Link>
          </Button>
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
            <OpportunityCandidateCard
              key={item.ticker}
              item={{
                ...item,
                reasons: item.reasons.slice(0, 2),
                missing_confirmations: item.missing_confirmations.slice(0, 2),
              }}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}
