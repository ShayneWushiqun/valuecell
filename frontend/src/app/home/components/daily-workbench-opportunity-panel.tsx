import { Link } from "react-router";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { AShareDailyWorkbenchOverview } from "@/types/ashare-daily-workbench";

export default function DailyWorkbenchOpportunityPanel({
  opportunities,
}: {
  opportunities: AShareDailyWorkbenchOverview["top_opportunities"];
}) {
  return (
    <section className="rounded-2xl border bg-background p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="font-semibold text-lg">今日机会摘要</p>
          <p className="text-muted-foreground text-sm">只看前 3 到 5 条重点机会，详细确认再去机会池。</p>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to="/home/opportunities">查看全部机会池</Link>
        </Button>
      </div>
      <div className="space-y-3">
        {opportunities.length ? (
          opportunities.map((item) => (
            <div key={item.ticker} className="rounded-xl border p-4">
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium">{item.display_name}</p>
                <Badge variant="outline">{item.topic_name || "未分类题材"}</Badge>
                <Badge variant="secondary">{item.candidate_state}</Badge>
                <Badge variant="outline">优先分 {item.priority_score}</Badge>
              </div>
              <p className="mt-2 text-muted-foreground text-sm">
                当前动作：{item.action || "继续观察"}
              </p>
              <p className="mt-1 text-sm">可交易状态：{item.tradeability_state}</p>
            </div>
          ))
        ) : (
          <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
            暂无重点机会摘要
          </div>
        )}
      </div>
    </section>
  );
}
