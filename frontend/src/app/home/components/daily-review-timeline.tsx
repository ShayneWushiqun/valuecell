import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { AShareDailySnapshotListItem } from "@/types/ashare-daily-snapshot";

export default function DailyReviewTimeline({
  items,
  selectedDate,
  onSelect,
}: {
  items: AShareDailySnapshotListItem[];
  selectedDate: string | null;
  onSelect: (snapshotDate: string) => void;
}) {
  return (
    <section className="rounded-2xl border bg-background p-5">
      <p className="font-semibold text-lg">快照时间线</p>
      <div className="mt-4 space-y-3">
        {items.length ? (
          items.map((item) => (
            <button
              key={item.snapshot_date}
              type="button"
              onClick={() => onSelect(item.snapshot_date)}
              className={`w-full rounded-xl border p-4 text-left ${
                selectedDate === item.snapshot_date ? "border-primary" : ""
              }`}
            >
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium">{item.snapshot_date}</p>
                <Badge variant="outline">
                  {item.market_digest.market_state || "待观察"}
                </Badge>
                <Badge variant="outline">
                  {item.market_digest.emotion_stage || "情绪待观察"}
                </Badge>
              </div>
              <div className="mt-3 grid gap-2 text-sm md:grid-cols-4">
                <p>风险回避 {item.attention_digest.risk_alert_count || 0}</p>
                <p>接近可参与窗口 {item.attention_digest.near_entry_count || 0}</p>
                <p>需处理持仓 {item.attention_digest.holding_risk_count || 0}</p>
                <p>保护利润 {item.attention_digest.holding_profit_protection_count || 0}</p>
              </div>
              <div className="mt-3 space-y-1 text-muted-foreground text-sm">
                {item.brief_action_queue.slice(0, 2).map((queue) => (
                  <p key={queue}>- {queue}</p>
                ))}
              </div>
            </button>
          ))
        ) : (
          <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
            暂无历史快照，请先记录今日快照。
          </div>
        )}
      </div>
      {items.length > 0 ? (
        <div className="mt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onSelect(items[0].snapshot_date)}
          >
            回到最近快照
          </Button>
        </div>
      ) : null}
    </section>
  );
}
