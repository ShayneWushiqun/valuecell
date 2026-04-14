import { Badge } from "@/components/ui/badge";
import type { AShareDailyWorkbenchOverview } from "@/types/ashare-daily-workbench";

export default function DailyWorkbenchMarketPanel({
  marketDigest,
}: {
  marketDigest: AShareDailyWorkbenchOverview["market_digest"];
}) {
  return (
    <section className="rounded-2xl border bg-background p-5">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-semibold text-lg">市场摘要</p>
        {marketDigest.temperature_score !== null ? (
          <Badge variant="outline">温度分 {marketDigest.temperature_score}</Badge>
        ) : null}
      </div>
      <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div>
          <p className="text-muted-foreground text-sm">市场状态</p>
          <p className="mt-1 font-medium">{marketDigest.market_state || "--"}</p>
        </div>
        <div>
          <p className="text-muted-foreground text-sm">情绪阶段</p>
          <p className="mt-1 font-medium">{marketDigest.emotion_stage || "--"}</p>
        </div>
        <div className="md:col-span-2">
          <p className="text-muted-foreground text-sm">操作节奏</p>
          <p className="mt-1 font-medium">{marketDigest.action_rhythm || "--"}</p>
        </div>
      </div>
      <p className="mt-4 text-muted-foreground text-sm">
        {marketDigest.summary || "暂无可用市场摘要"}
      </p>
    </section>
  );
}
