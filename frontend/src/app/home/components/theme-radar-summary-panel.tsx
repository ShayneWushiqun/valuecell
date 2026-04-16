import type { ThemeRadarOverview } from "@/types/theme-radar";

export default function ThemeRadarSummaryPanel({
  summary,
}: {
  summary: ThemeRadarOverview["summary"];
}) {
  const cards = [
    { label: "加强题材", value: summary.strengthen_count },
    { label: "活跃题材", value: summary.active_theme_count },
    { label: "分歧题材", value: summary.split_count },
    { label: "退潮题材", value: summary.fading_count },
    { label: "命中偏好", value: summary.preferred_theme_hit_count },
    { label: "观察池共振", value: summary.watchlist_resonance_count },
  ];

  return (
    <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
      {cards.map((card) => (
        <div key={card.label} className="rounded-2xl border bg-background p-4">
          <p className="text-muted-foreground text-sm">{card.label}</p>
          <p className="mt-2 font-semibold text-2xl">{card.value}</p>
        </div>
      ))}
    </section>
  );
}
