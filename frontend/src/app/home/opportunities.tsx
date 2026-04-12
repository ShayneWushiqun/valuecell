import { useGetDecisionAlertSummary } from "@/api/decision-alert";
import BackButton from "@valuecell/button/back-button";
import { useMemo, useState } from "react";
import { useGetEntryTimingSignals } from "@/api/entry-timing";
import { useGetOpportunityCandidates } from "@/api/opportunity-pool";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { DecisionAlertSummaryPanel, OpportunityCandidateCard } from "./components";

const FILTER_OPTIONS = [
  "全部",
  "高优先级",
  "候选买点",
  "仅适合持有",
  "暂不参与",
] as const;

type OpportunityFilter = (typeof FILTER_OPTIONS)[number];

const GROUP_ORDER = ["A", "B", "C"] as const;

export default function Opportunities() {
  const [activeFilter, setActiveFilter] = useState<OpportunityFilter>("全部");
  const {
    data: opportunityPool,
    isLoading,
    isError,
  } = useGetOpportunityCandidates();
  const {
    data: entryTimingSignals,
    isLoading: entryTimingLoading,
    isError: entryTimingError,
  } = useGetEntryTimingSignals();
  const {
    data: decisionAlertSummary,
  } = useGetDecisionAlertSummary();

  const filteredItems = useMemo(() => {
    const items = opportunityPool?.items || [];
    if (activeFilter === "全部") return items;
    if (activeFilter === "高优先级") {
      return items.filter((item) => item.candidate_state.includes("高优先级"));
    }
    return items.filter((item) => item.candidate_state === activeFilter);
  }, [activeFilter, opportunityPool?.items]);

  const groupedItems = useMemo(() => {
    return GROUP_ORDER.map((bucket) => ({
      bucket,
      items: filteredItems.filter((item) => item.ranking_bucket === bucket),
    })).filter((group) => group.items.length > 0);
  }, [filteredItems]);

  const signalByTicker = useMemo(
    () =>
      new Map((entryTimingSignals?.items || []).map((signal) => [signal.ticker, signal])),
    [entryTimingSignals?.items],
  );

  const topSignals = useMemo(
    () => (entryTimingSignals?.items || []).slice(0, 4),
    [entryTimingSignals?.items],
  );

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />

      <div className="space-y-3">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h1 className="font-semibold text-2xl">机会池</h1>
            <p className="mt-1 text-muted-foreground text-sm">
              候选机会不等于买入建议，当前页面只用于集中查看候选、风险条件与等待确认项。
            </p>
          </div>
          {opportunityPool?.source_summary ? (
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary">
                候选 {opportunityPool.source_summary.candidate_count}
              </Badge>
              <Badge variant="outline">
                自选来源 {opportunityPool.source_summary.watchlist_count}
              </Badge>
              <Badge variant="outline">
                题材来源 {opportunityPool.source_summary.theme_candidate_count}
              </Badge>
              {decisionAlertSummary?.count ? (
                <Badge variant="outline">提醒 {decisionAlertSummary.count}</Badge>
              ) : null}
            </div>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-2">
          {FILTER_OPTIONS.map((filterOption) => (
            <Button
              key={filterOption}
              size="sm"
              variant={activeFilter === filterOption ? "default" : "outline"}
              onClick={() => setActiveFilter(filterOption)}
            >
              {filterOption}
            </Button>
          ))}
        </div>
      </div>

      <DecisionAlertSummaryPanel />

      <div className="rounded-2xl border bg-background p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="font-medium text-base">买点裁决</h2>
            <p className="mt-1 text-muted-foreground text-sm">
              仅提供保守的规则版判断，不构成直接买入建议。
            </p>
          </div>
          {entryTimingLoading ? <Spinner className="size-4" /> : null}
        </div>

        {!entryTimingLoading && (entryTimingError || !entryTimingSignals?.available || !topSignals.length) ? (
          <div className="mt-3 rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
            暂无买点裁决信号
          </div>
        ) : null}

        {!entryTimingLoading && !entryTimingError && topSignals.length ? (
          <div className="mt-3 grid gap-3 xl:grid-cols-2">
            {topSignals.map((signal) => (
              <div key={signal.ticker} className="rounded-xl border bg-card p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-medium text-sm">{signal.display_name}</p>
                  <Badge variant="secondary">{signal.action}</Badge>
                  <Badge variant="outline">置信度 {signal.confidence}</Badge>
                </div>
                <p className="mt-2 text-muted-foreground text-sm">{signal.summary}</p>
              </div>
            ))}
          </div>
        ) : null}
      </div>

      {isLoading ? (
        <div className="flex min-h-64 items-center justify-center">
          <Spinner className="size-5" />
        </div>
      ) : null}

      {!isLoading && (isError || !opportunityPool?.available || !filteredItems.length) ? (
        <div className="rounded-xl border border-dashed p-6 text-muted-foreground text-sm">
          {opportunityPool?.empty_message || "暂无可用机会池候选"}
        </div>
      ) : null}

      {!isLoading && !isError && groupedItems.length ? (
        <div className="space-y-6">
          {groupedItems.map((group) => (
            <section key={group.bucket} className="space-y-3">
              <div className="flex items-center gap-2">
                <Badge variant="secondary">Bucket {group.bucket}</Badge>
                <p className="text-muted-foreground text-sm">
                  {group.bucket === "A"
                    ? "优先级更高，但仍需等待确认"
                    : group.bucket === "B"
                      ? "保持重点观察，择机确认"
                      : "先观察，不急于参与"}
                </p>
              </div>
              <div className="grid gap-4 xl:grid-cols-2">
                {group.items.map((item) => (
                  <OpportunityCandidateCard
                    key={item.ticker}
                    item={item}
                    signal={signalByTicker.get(item.ticker) ?? null}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : null}
    </div>
  );
}
