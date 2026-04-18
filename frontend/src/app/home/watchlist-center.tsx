import BackButton from "@valuecell/button/back-button";
import { useMemo, useState } from "react";
import { Link } from "react-router";
import { useGetWatchlistCenterOverview } from "@/api/watchlist-center";
import WatchlistCenterList from "@/app/home/components/watchlist-center-list";
import WatchlistCenterSummaryPanel from "@/app/home/components/watchlist-center-summary-panel";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import type { WatchlistCenterItem } from "@/types/watchlist-center";

const FILTER_OPTIONS = [
  "全部",
  "重点观察",
  "主线共振",
  "已进机会池",
  "已有提醒",
  "已持仓",
  "普通观察",
] as const;

type WatchlistFilter = (typeof FILTER_OPTIONS)[number];

const filterItems = (
  items: WatchlistCenterItem[],
  activeFilter: WatchlistFilter,
) => {
  if (activeFilter === "全部") return items;
  if (activeFilter === "重点观察") {
    return items.filter((item) => item.observation_priority === "高");
  }
  if (activeFilter === "主线共振") {
    return items.filter((item) => item.has_theme_resonance);
  }
  if (activeFilter === "已进机会池") {
    return items.filter((item) => item.has_opportunity_link);
  }
  if (activeFilter === "已有提醒") {
    return items.filter((item) => item.has_active_alert);
  }
  if (activeFilter === "已持仓") {
    return items.filter((item) => item.has_holding);
  }
  return items.filter((item) => item.observation_priority === "低");
};

export default function WatchlistCenter() {
  const [activeFilter, setActiveFilter] = useState<WatchlistFilter>("全部");
  const { data, isLoading, isError } = useGetWatchlistCenterOverview();

  const filteredItems = useMemo(
    () => filterItems(data?.items || [], activeFilter),
    [activeFilter, data?.items],
  );

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-semibold text-2xl">观察池中心</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            集中看自选观察、题材共振、提醒联动和持仓关系。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to="/home/daily-workbench">返回总控台</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/theme-radar">去题材雷达</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/opportunities">去机会池</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/stock-analysis">新建分析线程</Link>
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex min-h-72 items-center justify-center">
          <Spinner className="size-6" />
        </div>
      ) : null}

      {!isLoading && (isError || !data?.available) ? (
        <div className="rounded-xl border border-dashed p-6 text-muted-foreground text-sm">
          {data?.empty_message || "暂无可用观察池中心数据"}
        </div>
      ) : null}

      {!isLoading && !isError && data?.available ? (
        <>
          <WatchlistCenterSummaryPanel summary={data.summary} />

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

          {filteredItems.length ? (
            <WatchlistCenterList items={filteredItems} />
          ) : (
            <div className="rounded-xl border border-dashed p-6 text-muted-foreground text-sm">
              当前筛选下暂无观察项，先保持常规观察。
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
