import BackButton from "@valuecell/button/back-button";
import { useMemo, useState } from "react";
import { Link } from "react-router";
import { useGetThemeRadarOverview } from "@/api/theme-radar";
import ThemeRadarGrid from "@/app/home/components/theme-radar-grid";
import ThemeRadarSummaryPanel from "@/app/home/components/theme-radar-summary-panel";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import type { ThemeRadarItem } from "@/types/theme-radar";

const FILTER_OPTIONS = [
  "全部",
  "加强",
  "活跃",
  "分歧",
  "退潮",
  "命中偏好",
  "与观察池共振",
  "与机会池共振",
] as const;

type ThemeRadarFilter = (typeof FILTER_OPTIONS)[number];

const filterItems = (items: ThemeRadarItem[], activeFilter: ThemeRadarFilter) => {
  if (activeFilter === "全部") return items;
  if (activeFilter === "命中偏好") {
    return items.filter((item) => item.has_preference_match);
  }
  if (activeFilter === "与观察池共振") {
    return items.filter((item) => item.watchlist_resonance_count > 0);
  }
  if (activeFilter === "与机会池共振") {
    return items.filter((item) => item.opportunity_resonance_count > 0);
  }
  return items.filter((item) => item.theme_state === activeFilter);
};

export default function ThemeRadar() {
  const [activeFilter, setActiveFilter] = useState<ThemeRadarFilter>("全部");
  const { data, isLoading, isError } = useGetThemeRadarOverview();

  const filteredItems = useMemo(
    () => filterItems(data?.items || [], activeFilter),
    [activeFilter, data?.items],
  );

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-semibold text-2xl">题材雷达</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            先看方向强弱和参与边界，再决定是否继续跟踪相关个股。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to="/home/daily-workbench">返回总控台</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/watchlist-center">去观察池中心</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/opportunities">去机会池</Link>
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
          {data?.empty_message || "暂无可用题材雷达数据"}
        </div>
      ) : null}

      {!isLoading && !isError && data?.available ? (
        <>
          <ThemeRadarSummaryPanel summary={data.summary} />

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
            <ThemeRadarGrid items={filteredItems} />
          ) : (
            <div className="rounded-xl border border-dashed p-6 text-muted-foreground text-sm">
              当前筛选下暂无题材项，先保持保守观察。
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
