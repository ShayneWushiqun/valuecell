import { Link } from "react-router";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { AShareDailyWorkbenchOverview } from "@/types/ashare-daily-workbench";

const getHoldingActionClassName = (action: string) => {
  if (action === "纪律止损") return "bg-red-500/10 text-red-500";
  if (action === "保护利润") return "bg-amber-500/10 text-amber-600";
  if (action === "减仓观察") return "bg-orange-500/10 text-orange-500";
  if (action === "继续持有") return "bg-emerald-500/10 text-emerald-500";
  return "bg-blue-500/10 text-blue-500";
};

function HoldingList({
  title,
  items,
}: {
  title: string;
  items:
    | AShareDailyWorkbenchOverview["top_holdings_to_handle"]
    | AShareDailyWorkbenchOverview["top_holdings_stable"];
}) {
  return (
    <div className="space-y-3 rounded-xl border p-4">
      <p className="font-medium text-sm">{title}</p>
      {items.length ? (
        items.map((item) => (
          <div key={`${item.holding_id}-${item.ticker}`} className="rounded-lg border p-3">
            <div className="flex flex-wrap items-center gap-2">
              <p className="font-medium">{item.asset_name}</p>
              <Badge className={getHoldingActionClassName(item.action)}>{item.action}</Badge>
              <Badge variant="outline">置信度 {item.confidence}</Badge>
            </div>
            <p className="mt-2 text-sm">{item.summary}</p>
            <p className="mt-1 text-muted-foreground text-sm">{item.profit_protection_view}</p>
          </div>
        ))
      ) : (
        <div className="rounded-lg border border-dashed p-3 text-muted-foreground text-sm">
          暂无相关持仓摘要
        </div>
      )}
    </div>
  );
}

export default function DailyWorkbenchHoldingPanel({
  toHandle,
  stable,
}: {
  toHandle: AShareDailyWorkbenchOverview["top_holdings_to_handle"];
  stable: AShareDailyWorkbenchOverview["top_holdings_stable"];
}) {
  return (
    <section className="rounded-2xl border bg-background p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="font-semibold text-lg">今日持仓处理摘要</p>
          <p className="text-muted-foreground text-sm">先看需要处理的仓位，再看相对稳定的持仓。</p>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to="/home">查看全部持仓</Link>
        </Button>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <HoldingList title="需要优先处理" items={toHandle} />
        <HoldingList title="相对稳定持仓" items={stable} />
      </div>
    </section>
  );
}
