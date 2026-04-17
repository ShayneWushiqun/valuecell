export default function DecisionContextSummaryPanel({
  summary,
}: {
  summary: {
    total: number;
    highRisk: number;
    highDisagreement: number;
    watchable: number;
  };
}) {
  const cards = [
    { label: "总窗口数", value: summary.total },
    { label: "高风险窗口", value: summary.highRisk },
    { label: "高分歧窗口", value: summary.highDisagreement },
    { label: "可继续观察", value: summary.watchable },
  ];

  return (
    <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <div key={card.label} className="rounded-2xl border bg-background p-4">
          <p className="text-muted-foreground text-sm">{card.label}</p>
          <p className="mt-2 font-semibold text-2xl">{card.value}</p>
        </div>
      ))}
    </section>
  );
}
