import { useMemo } from "react";
import { useGetDecisionAlertSummary } from "@/api/decision-alert";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";

const getAlertTypeClassName = (alertType: string) => {
  if (alertType.includes("买点接近")) return "bg-emerald-500/10 text-emerald-500";
  if (alertType.includes("等待确认")) return "bg-blue-500/10 text-blue-500";
  if (alertType.includes("持有观察")) return "bg-orange-500/10 text-orange-500";
  if (alertType.includes("风险回避")) return "bg-red-500/10 text-red-500";
  return "bg-muted text-muted-foreground";
};

const getPriorityClassName = (priority: string) => {
  if (priority === "high") return "bg-red-500/10 text-red-500";
  if (priority === "medium") return "bg-orange-500/10 text-orange-500";
  return "bg-muted text-muted-foreground";
};

export default function DecisionAlertSummaryPanel() {
  const {
    data: decisionAlertSummary,
    isLoading,
    isError,
  } = useGetDecisionAlertSummary();

  const visibleAlerts = useMemo(
    () => (decisionAlertSummary?.items || []).slice(0, 4),
    [decisionAlertSummary?.items],
  );

  return (
    <div className="rounded-2xl border bg-background p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="font-medium text-base">今日提醒摘要</h2>
          <p className="mt-1 text-muted-foreground text-sm">
            聚合展示关键变化，帮助你先看什么需要继续确认、持有观察或风险回避。
          </p>
        </div>
        {isLoading ? <Spinner className="size-4" /> : null}
      </div>

      {!isLoading && (isError || !decisionAlertSummary?.available || !visibleAlerts.length) ? (
        <div className="mt-3 rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
          暂无提醒摘要
        </div>
      ) : null}

      {!isLoading && !isError && visibleAlerts.length ? (
        <div className="mt-3 grid gap-3 xl:grid-cols-2">
          {visibleAlerts.map((alert) => (
            <div
              key={`${alert.ticker}-${alert.alert_type}`}
              className={`rounded-xl border p-3 ${
                alert.alert_type === "风险回避"
                  ? "border-red-500/20 bg-red-500/5"
                  : "bg-card"
              }`}
            >
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium text-sm">{alert.display_name}</p>
                <Badge className={getAlertTypeClassName(alert.alert_type)}>
                  {alert.alert_type}
                </Badge>
                <Badge className={getPriorityClassName(alert.priority)}>
                  {alert.priority}
                </Badge>
                <Badge variant="outline">置信度 {alert.confidence}</Badge>
              </div>

              <p className="mt-2 font-medium text-sm">{alert.title}</p>
              <p className="mt-1 text-muted-foreground text-sm">{alert.body}</p>
              <p className="mt-2 text-sm">
                <span className="font-medium">下一步：</span>
                {alert.next_action}
              </p>

              {alert.reasons.length ? (
                <div className="mt-2 space-y-1 text-muted-foreground text-sm">
                  {alert.reasons.slice(0, 2).map((reason) => (
                    <p key={reason}>- {reason}</p>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
