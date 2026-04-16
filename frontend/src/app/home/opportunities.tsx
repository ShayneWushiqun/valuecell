import { useGetDecisionAlertSummary } from "@/api/decision-alert";
import BackButton from "@valuecell/button/back-button";
import { useMemo, useState } from "react";
import { Link } from "react-router";
import { useGetEntryTimingSignals } from "@/api/entry-timing";
import { useGetOpportunityCandidates } from "@/api/opportunity-pool";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import {
  DecisionAlertSummaryPanel,
  EntryTimingSummaryPanel,
  OpportunityCandidateCard,
} from "./components";

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

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />

      <div className="space-y-3">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h1 className="font-semibold text-2xl">机会池</h1>
            <p className="mt-1 text-muted-foreground text-sm">
              先看提醒，再看买点裁决，最后回到全部候选，不把任何摘要直接当成买入指令。
            </p>
          </div>
          <div className="flex flex-col items-start gap-3 lg:items-end">
            <div className="flex flex-wrap gap-2">
              <Button asChild variant="outline">
                <Link to="/home/daily-workbench">返回总控台</Link>
              </Button>
              <Button asChild variant="outline">
                <Link to="/home/theme-radar">去题材雷达</Link>
              </Button>
              <Button asChild variant="outline">
                <Link to="/home/watchlist-center">去观察池中心</Link>
              </Button>
              <Button asChild variant="outline">
                <Link to="/home/alerts">提醒中心</Link>
              </Button>
              <Button asChild variant="outline">
                <Link to="/home/strategy-preferences">策略偏好</Link>
              </Button>
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
                {opportunityPool.source_summary.preference_profile_applied ? (
                  <Badge variant="outline">
                    偏好 {opportunityPool.source_summary.preference_profile_applied}
                  </Badge>
                ) : null}
              </div>
            ) : null}
          </div>
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
      <EntryTimingSummaryPanel />

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
