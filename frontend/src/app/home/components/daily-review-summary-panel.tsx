import type { AShareDailySnapshotListItem } from "@/types/ashare-daily-snapshot";

const formatDelta = (current?: number, previous?: number) => {
  const currentValue = current || 0;
  const previousValue = previous || 0;
  if (currentValue > previousValue) return "上升";
  if (currentValue < previousValue) return "下降";
  return "持平";
};

export default function DailyReviewSummaryPanel({
  current,
  previous,
}: {
  current: AShareDailySnapshotListItem | null;
  previous: AShareDailySnapshotListItem | null;
}) {
  if (!current || !previous) {
    return (
      <section className="rounded-2xl border bg-background p-5">
        <p className="font-semibold text-lg">最近变化摘要</p>
        <p className="mt-2 text-muted-foreground text-sm">
          至少需要 2 天快照，才能对比最近变化。
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border bg-background p-5">
      <p className="font-semibold text-lg">最近变化摘要</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-xl border p-4">
          <p className="text-muted-foreground text-sm">风险回避变化</p>
          <p className="mt-2 font-medium">
            {formatDelta(
              current.attention_digest.risk_alert_count,
              previous.attention_digest.risk_alert_count,
            )}
          </p>
        </div>
        <div className="rounded-xl border p-4">
          <p className="text-muted-foreground text-sm">接近可参与窗口变化</p>
          <p className="mt-2 font-medium">
            {formatDelta(
              current.attention_digest.near_entry_count,
              previous.attention_digest.near_entry_count,
            )}
          </p>
        </div>
        <div className="rounded-xl border p-4">
          <p className="text-muted-foreground text-sm">需处理持仓变化</p>
          <p className="mt-2 font-medium">
            {formatDelta(
              current.attention_digest.holding_risk_count,
              previous.attention_digest.holding_risk_count,
            )}
          </p>
        </div>
        <div className="rounded-xl border p-4">
          <p className="text-muted-foreground text-sm">市场状态变化</p>
          <p className="mt-2 font-medium">
            {current.market_digest.market_state || "--"}
            {" / "}
            {previous.market_digest.market_state || "--"}
          </p>
        </div>
      </div>
    </section>
  );
}
