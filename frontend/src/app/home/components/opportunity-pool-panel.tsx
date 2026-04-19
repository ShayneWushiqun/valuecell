import { useMemo } from "react";
import { Link } from "react-router";
import { useGetOpportunityCandidates } from "@/api/opportunity-pool";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { isApiNetworkError } from "@/lib/api-client";
import OpportunityCandidateCard from "./opportunity-candidate-card";

export default function OpportunityPoolPanel() {
  const {
    data: opportunityPool,
    isLoading,
    isError,
    isFetching,
    error,
    refetch,
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

      {!!visibleItems.length && isFetching ? (
        <p className="mt-4 text-center text-muted-foreground text-xs">
          已展示上次结果，正在后台刷新机会池。
        </p>
      ) : null}

      {!!visibleItems.length && isError ? (
        <Alert className="mt-4">
          <AlertTitle>当前先使用缓存结果</AlertTitle>
          <AlertDescription>
            <p>
              {isApiNetworkError(error)
                ? "网络波动，当前先显示上次机会池结果。"
                : "机会池刷新失败，当前先显示上次结果。"}
            </p>
            <Button size="sm" variant="outline" onClick={() => void refetch()}>
              重试
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}

      {!isLoading && (!visibleItems.length && (isError || !opportunityPool?.available)) ? (
        <div className="mt-4 rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
          {opportunityPool?.empty_message || "暂无可用机会池候选"}
        </div>
      ) : null}

      {!isLoading && visibleItems.length ? (
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
