import { Badge } from "@/components/ui/badge";
import type { WatchlistCenterItem } from "@/types/watchlist-center";

const formatPercent = (value?: number | null) => {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
};

const getPriorityClassName = (priority: string) => {
  if (priority === "高") return "bg-emerald-500/10 text-emerald-500";
  if (priority === "中") return "bg-blue-500/10 text-blue-500";
  return "bg-muted text-muted-foreground";
};

export default function WatchlistCenterCard({
  item,
}: {
  item: WatchlistCenterItem;
}) {
  return (
    <div className="rounded-2xl border bg-background p-4">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-semibold text-base">{item.display_name}</p>
        <Badge variant="outline">{item.ticker}</Badge>
        <Badge className={getPriorityClassName(item.observation_priority)}>
          观察优先级 {item.observation_priority}
        </Badge>
        <Badge variant="secondary">{item.status}</Badge>
        {item.has_holding ? <Badge variant="outline">已持仓</Badge> : null}
      </div>

      <div className="mt-3 flex flex-wrap gap-2 text-muted-foreground text-xs">
        <span>{item.watchlist_name}</span>
        {item.theme_name ? <span>题材 {item.theme_name}</span> : null}
        <span>最新价 {item.latest_price || "--"}</span>
        <span>涨跌 {formatPercent(item.change_percent)}</span>
      </div>

      <p className="mt-3 text-sm">{item.reason}</p>
      <p className="mt-2 text-muted-foreground text-sm">{item.quick_note}</p>

      <div className="mt-3 flex flex-wrap gap-2">
        <Badge variant="outline">{item.tradeability_state}</Badge>
        <Badge variant="outline">预期差 {item.expectation_gap_level}</Badge>
        <Badge variant="outline">{item.role_label}</Badge>
        <Badge variant="outline">趋势 {item.trend_quality}</Badge>
        {item.linked_candidate_state ? (
          <Badge variant="outline">机会池 {item.linked_candidate_state}</Badge>
        ) : null}
        {item.linked_judge_action ? (
          <Badge variant="outline">裁决 {item.linked_judge_action}</Badge>
        ) : null}
        {item.holding_action ? (
          <Badge variant="outline">持仓 {item.holding_action}</Badge>
        ) : null}
      </div>
    </div>
  );
}
