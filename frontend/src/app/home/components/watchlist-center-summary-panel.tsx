import type { WatchlistCenterOverview } from "@/types/watchlist-center";

export default function WatchlistCenterSummaryPanel({
  summary,
}: {
  summary: WatchlistCenterOverview["summary"];
}) {
  const cards = [
    { label: "总观察数", value: summary.total_count },
    { label: "重点观察", value: summary.focus_count },
    { label: "主线共振", value: summary.theme_resonance_count },
    { label: "已有提醒", value: summary.active_alert_count },
    { label: "已持仓关联", value: summary.holding_linked_count },
  ];

  return (
    <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
      {cards.map((card) => (
        <div key={card.label} className="rounded-2xl border bg-background p-4">
          <p className="text-muted-foreground text-sm">{card.label}</p>
          <p className="mt-2 font-semibold text-2xl">{card.value}</p>
        </div>
      ))}
    </section>
  );
}
