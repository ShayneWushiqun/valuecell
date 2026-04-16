import type { AShareDailySnapshotDetail } from "@/types/ashare-daily-snapshot";

function SectionList({
  title,
  items,
  render,
}: {
  title: string;
  items: Record<string, unknown>[];
  render: (item: Record<string, unknown>) => string;
}) {
  return (
    <div className="rounded-xl border p-4">
      <p className="font-medium text-sm">{title}</p>
      <div className="mt-2 space-y-2 text-sm">
        {items.length ? (
          items.map((item) => (
            <p
              key={
                String(item.id || item.holding_id || item.ticker || item.title || render(item))
              }
            >
              {render(item)}
            </p>
          ))
        ) : (
          <p className="text-muted-foreground">暂无记录</p>
        )}
      </div>
    </div>
  );
}

export default function DailyReviewDetailPanel({
  snapshot,
}: {
  snapshot: AShareDailySnapshotDetail | null;
}) {
  if (!snapshot) {
    return (
      <section className="rounded-2xl border bg-background p-5">
        <p className="font-semibold text-lg">快照详情</p>
        <p className="mt-2 text-muted-foreground text-sm">
          请选择某一天的快照查看详情。
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border bg-background p-5">
      <div className="mb-4">
        <p className="font-semibold text-lg">快照详情</p>
        <p className="mt-1 text-muted-foreground text-sm">
          {snapshot.snapshot_date} 的市场、机会、提醒和持仓处理摘要。
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <div className="rounded-xl border p-4">
          <p className="font-medium text-sm">市场摘要</p>
          <div className="mt-2 space-y-1 text-sm">
            <p>市场状态：{snapshot.market_digest.market_state || "--"}</p>
            <p>情绪阶段：{snapshot.market_digest.emotion_stage || "--"}</p>
            <p>温度分：{snapshot.market_digest.temperature_score ?? "--"}</p>
            <p className="text-muted-foreground">{snapshot.market_digest.summary || "--"}</p>
          </div>
        </div>

        <div className="rounded-xl border p-4">
          <p className="font-medium text-sm">当天行动顺序</p>
          <div className="mt-2 space-y-1 text-sm">
            {snapshot.today_action_queue.length ? (
              snapshot.today_action_queue.map((item, index) => (
                <p key={`${item.title || "queue"}-${index}`}>
                  {index + 1}. {item.title || "--"}：{item.reason || "--"}
                </p>
              ))
            ) : (
              <p className="text-muted-foreground">暂无行动顺序摘要</p>
            )}
          </div>
        </div>

        <SectionList
          title="当天提醒摘要"
          items={snapshot.top_alerts}
          render={(item) =>
            `${String(item.display_name || item.ticker || "--")} / ${String(
              item.alert_type || "--",
            )} / ${String(item.title || "--")}`
          }
        />

        <SectionList
          title="当天机会摘要"
          items={snapshot.top_opportunities}
          render={(item) =>
            `${String(item.display_name || item.ticker || "--")} / ${String(
              item.candidate_state || "--",
            )} / 优先分 ${String(item.priority_score || "--")}`
          }
        />

        <SectionList
          title="当天需处理持仓"
          items={snapshot.top_holdings_to_handle}
          render={(item) =>
            `${String(item.asset_name || item.ticker || "--")} / ${String(
              item.action || "--",
            )} / ${String(item.summary || "--")}`
          }
        />

        <SectionList
          title="当天相对稳定持仓"
          items={snapshot.top_holdings_stable}
          render={(item) =>
            `${String(item.asset_name || item.ticker || "--")} / ${String(
              item.action || "--",
            )} / ${String(item.summary || "--")}`
          }
        />
      </div>
    </section>
  );
}
