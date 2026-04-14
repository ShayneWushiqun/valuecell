import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import type { AShareDailyWorkbenchOverview } from "@/types/ashare-daily-workbench";

export default function DailyWorkbenchActionQueue({
  items,
}: {
  items: AShareDailyWorkbenchOverview["today_action_queue"];
}) {
  return (
    <section className="rounded-2xl border bg-background p-5">
      <div className="mb-4">
        <p className="font-semibold text-lg">今日行动顺序</p>
        <p className="text-muted-foreground text-sm">
          这是工作流摘要，不构成交易指令。
        </p>
      </div>
      <div className="space-y-3">
        {items.map((item, index) => (
          <div key={`${item.title}-${index}`} className="rounded-xl border p-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="font-medium">
                  {index + 1}. {item.title}
                </p>
                <p className="mt-1 text-muted-foreground text-sm">{item.reason}</p>
              </div>
              <Button asChild size="sm" variant="outline">
                <Link to={item.target_path}>继续查看</Link>
              </Button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
