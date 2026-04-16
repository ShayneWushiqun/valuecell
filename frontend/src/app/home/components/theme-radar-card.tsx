import { Badge } from "@/components/ui/badge";
import type { ThemeRadarItem } from "@/types/theme-radar";

const getStateClassName = (state: string) => {
  if (state === "加强") return "bg-emerald-500/10 text-emerald-500";
  if (state === "活跃") return "bg-blue-500/10 text-blue-500";
  if (state === "分歧") return "bg-orange-500/10 text-orange-500";
  if (state === "退潮") return "bg-red-500/10 text-red-500";
  return "bg-muted text-muted-foreground";
};

export default function ThemeRadarCard({ item }: { item: ThemeRadarItem }) {
  return (
    <div className="rounded-2xl border bg-background p-4">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-semibold text-base">{item.theme_name}</p>
        <Badge className={getStateClassName(item.theme_state)}>{item.theme_state}</Badge>
        <Badge variant="outline">Rank {item.rank}</Badge>
        <Badge variant="outline">分数 {item.score}</Badge>
        {item.has_preference_match ? <Badge variant="secondary">命中偏好</Badge> : null}
      </div>

      <div className="mt-3 flex flex-wrap gap-2 text-muted-foreground text-xs">
        <span>热度 {item.hot_level}</span>
        <span>{item.preferred_market}</span>
        <span>观察池共振 {item.watchlist_resonance_count}</span>
        <span>机会池共振 {item.opportunity_resonance_count}</span>
      </div>

      <p className="mt-3 text-sm">{item.participation_hint}</p>
      <p className="mt-2 text-muted-foreground text-sm">{item.observation_summary}</p>

      <div className="mt-3 flex flex-wrap gap-2">
        {(item.risk_tags || []).map((tag) => (
          <Badge key={tag} variant="outline">
            {tag}
          </Badge>
        ))}
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <div className="rounded-xl border bg-card p-3">
          <p className="text-muted-foreground text-xs">代表股</p>
          <p className="mt-1 text-sm">{item.primary_representative || "暂无代表股"}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {item.representative_tickers.slice(0, 3).map((ticker) => (
              <Badge key={ticker} variant="secondary">
                {ticker}
              </Badge>
            ))}
          </div>
        </div>
        <div className="rounded-xl border bg-card p-3">
          <p className="text-muted-foreground text-xs">核心票</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {item.core_leaders_json.slice(0, 3).map((ticker) => (
              <Badge key={ticker} variant="secondary">
                {ticker}
              </Badge>
            ))}
          </div>
          {item.etf_hint ? (
            <p className="mt-2 text-muted-foreground text-xs">{item.etf_hint.summary}</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
