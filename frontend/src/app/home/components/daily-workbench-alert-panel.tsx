import { Link } from "react-router";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { AShareDailyWorkbenchOverview } from "@/types/ashare-daily-workbench";

const getAlertTypeClassName = (alertType: string) => {
  if (alertType === "风险回避") return "bg-red-500/10 text-red-500";
  if (alertType === "买点接近") return "bg-emerald-500/10 text-emerald-500";
  return "bg-muted text-muted-foreground";
};

export default function DailyWorkbenchAlertPanel({
  alerts,
}: {
  alerts: AShareDailyWorkbenchOverview["top_alerts"];
}) {
  return (
    <section className="rounded-2xl border bg-background p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="font-semibold text-lg">今日提醒摘要</p>
          <p className="text-muted-foreground text-sm">先看风险，再看确认，不把提醒当成交易指令。</p>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to="/home/alerts">查看全部提醒</Link>
        </Button>
      </div>
      <div className="space-y-3">
        {alerts.length ? (
          alerts.map((alert) => (
            <div key={alert.id || `${alert.ticker}-${alert.title}`} className="rounded-xl border p-4">
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium">{alert.display_name}</p>
                <Badge className={getAlertTypeClassName(alert.alert_type)}>{alert.alert_type}</Badge>
                <Badge variant="outline">{alert.priority}</Badge>
              </div>
              <p className="mt-2 text-sm">{alert.title}</p>
              <p className="mt-1 text-muted-foreground text-sm">{alert.body}</p>
              <p className="mt-2 text-sm">
                <span className="font-medium">下一步：</span>
                {alert.next_action}
              </p>
            </div>
          ))
        ) : (
          <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
            暂无优先提醒
          </div>
        )}
      </div>
    </section>
  );
}
