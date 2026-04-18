import BackButton from "@valuecell/button/back-button";
import { useMemo, useState } from "react";
import { Link } from "react-router";
import {
  useDismissDecisionAlert,
  useGetDecisionAlerts,
  useMarkAllDecisionAlertsRead,
  useMarkDecisionAlertRead,
  useRefreshDecisionAlerts,
} from "@/api/decision-alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

const FILTER_OPTIONS = [
  { key: "all", label: "全部", status: "all", alertType: undefined },
  { key: "unread", label: "未读", status: "unread", alertType: undefined },
  { key: "near", label: "买点接近", status: "all", alertType: "买点接近" },
  { key: "wait", label: "等待确认", status: "all", alertType: "等待确认" },
  { key: "hold", label: "持有观察", status: "all", alertType: "持有观察" },
  { key: "risk", label: "风险回避", status: "all", alertType: "风险回避" },
  { key: "dismissed", label: "已忽略", status: "dismissed", alertType: undefined },
] as const;

const getAlertTypeClassName = (alertType: string) => {
  if (alertType === "买点接近") return "bg-emerald-500/10 text-emerald-500";
  if (alertType === "等待确认") return "bg-blue-500/10 text-blue-500";
  if (alertType === "持有观察") return "bg-orange-500/10 text-orange-500";
  if (alertType === "风险回避") return "bg-red-500/10 text-red-500";
  return "bg-muted text-muted-foreground";
};

const getPriorityClassName = (priority: string) => {
  if (priority === "high") return "bg-red-500/10 text-red-500";
  if (priority === "medium") return "bg-orange-500/10 text-orange-500";
  return "bg-muted text-muted-foreground";
};

export default function Alerts() {
  const [activeFilterKey, setActiveFilterKey] = useState<(typeof FILTER_OPTIONS)[number]["key"]>(
    "all",
  );
  const activeFilter =
    FILTER_OPTIONS.find((option) => option.key === activeFilterKey) || FILTER_OPTIONS[0];

  const { data: allAlerts } = useGetDecisionAlerts({ status: "all", limit: 200 });
  const {
    data: filteredAlerts,
    isLoading,
    isError,
  } = useGetDecisionAlerts({
    status: activeFilter.status,
    alertType: activeFilter.alertType,
    limit: 50,
  });
  const refreshAlerts = useRefreshDecisionAlerts();
  const markAlertRead = useMarkDecisionAlertRead();
  const markAllRead = useMarkAllDecisionAlertsRead();
  const dismissAlert = useDismissDecisionAlert();

  const stats = useMemo(() => {
    const items = allAlerts?.items || [];
    return {
      total: allAlerts?.count || 0,
      unread: allAlerts?.unread_count || 0,
      risk: items.filter((item) => item.alert_type === "风险回避").length,
      near: items.filter((item) => item.alert_type === "买点接近").length,
    };
  }, [allAlerts]);

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />

      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-semibold text-2xl">提醒中心</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            提醒只用于观察和风控，不构成买入指令。优先看未读变化，再决定是否继续确认或回避。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to="/home/daily-workbench">返回总控台</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/opportunities">返回机会池</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/stock-analysis">新建分析线程</Link>
          </Button>
          <Button
            variant="outline"
            onClick={() => refreshAlerts.mutate()}
            disabled={refreshAlerts.isPending}
          >
            {refreshAlerts.isPending ? "刷新中..." : "刷新提醒"}
          </Button>
          <Button
            variant="outline"
            onClick={() => markAllRead.mutate()}
            disabled={markAllRead.isPending}
          >
            {markAllRead.isPending ? "处理中..." : "全部标记已读"}
          </Button>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border bg-background p-4">
          <p className="text-muted-foreground text-sm">全部提醒数</p>
          <p className="mt-2 font-semibold text-2xl">{stats.total}</p>
        </div>
        <div className="rounded-2xl border bg-background p-4">
          <p className="text-muted-foreground text-sm">未读数</p>
          <p className="mt-2 font-semibold text-2xl">{stats.unread}</p>
        </div>
        <div className="rounded-2xl border bg-background p-4">
          <p className="text-muted-foreground text-sm">风险回避数</p>
          <p className="mt-2 font-semibold text-2xl">{stats.risk}</p>
        </div>
        <div className="rounded-2xl border bg-background p-4">
          <p className="text-muted-foreground text-sm">买点接近数</p>
          <p className="mt-2 font-semibold text-2xl">{stats.near}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {FILTER_OPTIONS.map((filterOption) => (
          <Button
            key={filterOption.key}
            size="sm"
            variant={activeFilterKey === filterOption.key ? "default" : "outline"}
            onClick={() => setActiveFilterKey(filterOption.key)}
          >
            {filterOption.label}
          </Button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex min-h-64 items-center justify-center">
          <Spinner className="size-5" />
        </div>
      ) : null}

      {!isLoading && (isError || !filteredAlerts?.items.length) ? (
        <div className="rounded-xl border border-dashed p-6 text-muted-foreground text-sm">
          暂无提醒摘要
        </div>
      ) : null}

      {!isLoading && !isError && filteredAlerts?.items.length ? (
        <div className="space-y-4">
          {filteredAlerts.items.map((alert) => (
            <div
              key={alert.id || `${alert.ticker}-${alert.alert_type}`}
              className={`rounded-2xl border p-4 ${
                alert.alert_type === "风险回避"
                  ? "border-red-500/20 bg-red-500/5"
                  : "bg-background"
              }`}
            >
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium">{alert.display_name}</p>
                    <Badge className={getAlertTypeClassName(alert.alert_type)}>
                      {alert.alert_type}
                    </Badge>
                    <Badge className={getPriorityClassName(alert.priority)}>
                      {alert.priority}
                    </Badge>
                    <Badge variant="outline">置信度 {alert.confidence}</Badge>
                    {!alert.read_at && !alert.dismissed_at ? (
                      <Badge variant="secondary">未读</Badge>
                    ) : null}
                    {alert.dismissed_at ? <Badge variant="outline">已忽略</Badge> : null}
                  </div>
                  <p className="font-medium text-sm">{alert.title}</p>
                  <p className="text-muted-foreground text-sm">{alert.body}</p>
                  <p className="text-sm">
                    <span className="font-medium">下一步：</span>
                    {alert.next_action}
                  </p>
                  {alert.reasons.length ? (
                    <div className="space-y-1 text-muted-foreground text-sm">
                      {alert.reasons.slice(0, 2).map((reason) => (
                        <p key={reason}>- {reason}</p>
                      ))}
                    </div>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!alert.id || !!alert.read_at || markAlertRead.isPending}
                    onClick={() => {
                      if (alert.id) markAlertRead.mutate(alert.id);
                    }}
                  >
                    标记已读
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!alert.id || !!alert.dismissed_at || dismissAlert.isPending}
                    onClick={() => {
                      if (alert.id) dismissAlert.mutate(alert.id);
                    }}
                  >
                    忽略
                  </Button>
                  <Button asChild size="sm" variant="outline">
                    <Link
                      to={`/home/stock-analysis?sourceModule=alert&sourceRef=${encodeURIComponent(`${alert.ticker}|${alert.alert_type}`)}&createThread=1`}
                    >
                      以当前提醒新建线程
                    </Link>
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
