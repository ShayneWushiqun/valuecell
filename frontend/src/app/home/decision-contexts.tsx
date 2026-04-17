import BackButton from "@valuecell/button/back-button";
import { useMemo, useState } from "react";
import { Link } from "react-router";
import { useGetDecisionContextWindows, useRefreshDecisionContextWindows } from "@/api/decision-context-window";
import DecisionContextSummaryPanel from "@/app/home/components/decision-context-summary-panel";
import DecisionContextWindowCard from "@/app/home/components/decision-context-window-card";
import DecisionContextWindowDetail from "@/app/home/components/decision-context-window-detail";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import type { DecisionContextWindow } from "@/types/decision-context-window";

const FILTER_OPTIONS = [
  "全部",
  "持仓相关",
  "机会池相关",
  "观察池相关",
  "高风险",
  "高分歧",
  "近10日",
  "近20日",
  "近40日",
] as const;

type FilterOption = (typeof FILTER_OPTIONS)[number];

const filterItems = (items: DecisionContextWindow[], filter: FilterOption) => {
  if (filter === "全部") return items;
  if (filter === "持仓相关") return items.filter((item) => item.has_holding);
  if (filter === "机会池相关") return items.filter((item) => item.has_opportunity);
  if (filter === "观察池相关") return items.filter((item) => item.has_watchlist);
  if (filter === "高风险") return items.filter((item) => item.risk_level === "高");
  if (filter === "高分歧") return items.filter((item) => item.disagreement_level === "高");
  if (filter === "近10日") return items.filter((item) => item.window_size === 10);
  if (filter === "近20日") return items.filter((item) => item.window_size === 20);
  return items.filter((item) => item.window_size === 40);
};

export default function DecisionContexts() {
  const [activeFilter, setActiveFilter] = useState<FilterOption>("全部");
  const [selectedItem, setSelectedItem] = useState<DecisionContextWindow | null>(null);
  const { data, isLoading, isError } = useGetDecisionContextWindows({ limit: 120 });
  const refresh = useRefreshDecisionContextWindows();

  const filteredItems = useMemo(
    () => filterItems(data?.items || [], activeFilter),
    [data?.items, activeFilter],
  );

  const summary = useMemo(
    () => ({
      total: data?.count || 0,
      highRisk: (data?.items || []).filter((item) => item.risk_level === "高").length,
      highDisagreement: (data?.items || []).filter((item) => item.disagreement_level === "高").length,
      watchable: (data?.items || []).filter(
        (item) => item.risk_level !== "高" && item.disagreement_level !== "高",
      ).length,
    }),
    [data?.count, data?.items],
  );

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-semibold text-2xl">决策上下文页</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            系统化查看最近一段时间的支持、反对与风险链条，更适合做解释型判断。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            onClick={() => refresh.mutate(undefined)}
            disabled={refresh.isPending}
          >
            {refresh.isPending ? "刷新中..." : "刷新时间窗"}
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/daily-workbench">返回总控台</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/holding-lifecycle">去持仓周期中心</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/exit-risk-center">去卖点与风险中心</Link>
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex min-h-72 items-center justify-center">
          <Spinner className="size-6" />
        </div>
      ) : null}

      {!isLoading && (isError || !data?.count) ? (
        <div className="rounded-xl border border-dashed p-6 text-muted-foreground text-sm">
          暂无可用决策上下文时间窗，请先执行刷新。
        </div>
      ) : null}

      {!isLoading && !isError && !!data?.count ? (
        <>
          <DecisionContextSummaryPanel summary={summary} />
          <div className="flex flex-wrap gap-2">
            {FILTER_OPTIONS.map((option) => (
              <Button
                key={option}
                size="sm"
                variant={activeFilter === option ? "default" : "outline"}
                onClick={() => setActiveFilter(option)}
              >
                {option}
              </Button>
            ))}
          </div>
          {filteredItems.length ? (
            <div className="grid gap-4 xl:grid-cols-2">
              {filteredItems.map((item) => (
                <DecisionContextWindowCard
                  key={item.window_id}
                  item={item}
                  onSelect={setSelectedItem}
                />
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed p-6 text-muted-foreground text-sm">
              当前筛选下暂无窗口，先保持保守观察。
            </div>
          )}
        </>
      ) : null}

      <DecisionContextWindowDetail
        item={selectedItem}
        open={!!selectedItem}
        onOpenChange={(open) => {
          if (!open) setSelectedItem(null);
        }}
      />
    </div>
  );
}
