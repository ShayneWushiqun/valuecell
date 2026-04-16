import BackButton from "@valuecell/button/back-button";
import { useMemo, useState } from "react";
import { Link } from "react-router";
import { useGetHoldingExitSignal } from "@/api/holding-exit-signal";
import { useGetHoldingLifecycleOverview } from "@/api/holding-lifecycle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Spinner } from "@/components/ui/spinner";
import type { HoldingLifecycleItem } from "@/types/holding-lifecycle";

const STAGES = [
  "建仓观察期",
  "主升持有期",
  "分歧确认期",
  "退潮减仓期",
  "破逻辑退出期",
] as const;

const getStageClassName = (stage: string) => {
  if (stage === "破逻辑退出期") return "bg-red-500/10 text-red-500";
  if (stage === "退潮减仓期") return "bg-orange-500/10 text-orange-500";
  if (stage === "分歧确认期") return "bg-amber-500/10 text-amber-600";
  if (stage === "主升持有期") return "bg-emerald-500/10 text-emerald-500";
  return "bg-blue-500/10 text-blue-500";
};

function HoldingExitSignalPreviewDialog({
  holding,
  open,
  onOpenChange,
}: {
  holding: HoldingLifecycleItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { data, isLoading } = useGetHoldingExitSignal(holding?.holding_id || null, open);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{holding?.display_name || "持仓裁决"}</DialogTitle>
          <DialogDescription>
            这里展示当前持仓裁决摘要，不构成交易指令。
          </DialogDescription>
        </DialogHeader>
        {isLoading ? (
          <div className="flex min-h-32 items-center justify-center">
            <Spinner className="size-5" />
          </div>
        ) : !data ? (
          <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
            暂无可用持仓裁决。
          </div>
        ) : (
          <div className="space-y-4">
            <div className="rounded-xl border bg-card p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="secondary">{data.action}</Badge>
                <Badge variant="outline">置信度 {data.confidence}</Badge>
              </div>
              <p className="mt-3 text-sm">{data.summary}</p>
              <p className="mt-2 text-muted-foreground text-sm">{data.thesis}</p>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-xl border bg-card p-4">
                <p className="font-medium text-sm">失效条件</p>
                <div className="mt-2 space-y-1 text-muted-foreground text-sm">
                  {data.invalid_conditions.map((item) => (
                    <p key={item}>- {item}</p>
                  ))}
                </div>
              </div>
              <div className="rounded-xl border bg-card p-4">
                <p className="font-medium text-sm">风控提示</p>
                <div className="mt-2 space-y-1 text-muted-foreground text-sm">
                  {data.risk_controls.map((item) => (
                    <p key={item}>- {item}</p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function HoldingLifecycle() {
  const { data, isLoading, isError } = useGetHoldingLifecycleOverview();
  const [selectedHolding, setSelectedHolding] = useState<HoldingLifecycleItem | null>(null);

  const groupedItems = useMemo(
    () =>
      Object.fromEntries(
        STAGES.map((stage) => [
          stage,
          (data?.items || []).filter((item) => item.lifecycle_stage === stage),
        ]),
      ) as Record<string, HoldingLifecycleItem[]>,
    [data?.items],
  );

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-semibold text-2xl">持仓周期中心</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            先看每只持仓当前所处阶段，再决定下一步处理顺序。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to="/home/daily-workbench">返回总控台</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/exit-risk-center">去卖点与风险中心</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/daily-review">去复盘中心</Link>
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex min-h-72 items-center justify-center">
          <Spinner className="size-6" />
        </div>
      ) : null}

      {!isLoading && (isError || !data?.available) ? (
        <div className="rounded-xl border border-dashed p-6 text-muted-foreground text-sm">
          {data?.empty_message || "暂无可用持仓周期数据"}
        </div>
      ) : null}

      {!isLoading && !isError && data?.available ? (
        <>
          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border bg-background p-4">
              <p className="text-muted-foreground text-sm">总持仓数</p>
              <p className="mt-2 font-semibold text-2xl">{data.summary.total_count}</p>
            </div>
            <div className="rounded-2xl border bg-background p-4">
              <p className="text-muted-foreground text-sm">需要处理</p>
              <p className="mt-2 font-semibold text-2xl">{data.summary.need_attention_count}</p>
            </div>
            <div className="rounded-2xl border bg-background p-4">
              <p className="text-muted-foreground text-sm">主升持有</p>
              <p className="mt-2 font-semibold text-2xl">{data.summary.major_hold_count}</p>
            </div>
            <div className="rounded-2xl border bg-background p-4">
              <p className="text-muted-foreground text-sm">高风险</p>
              <p className="mt-2 font-semibold text-2xl">{data.summary.high_risk_count}</p>
            </div>
          </section>

          <div className="space-y-5">
            {STAGES.map((stage) => (
              <section key={stage} className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="font-semibold text-lg">{stage}</p>
                  <Badge variant="outline">{groupedItems[stage].length} 项</Badge>
                </div>
                {groupedItems[stage].length ? (
                  <div className="grid gap-4 xl:grid-cols-2">
                    {groupedItems[stage].map((item) => (
                      <div key={item.holding_id} className="rounded-2xl border bg-background p-4">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-semibold text-base">{item.display_name}</p>
                          <Badge variant="outline">{item.ticker}</Badge>
                          <Badge className={getStageClassName(item.lifecycle_stage)}>
                            {item.lifecycle_stage}
                          </Badge>
                          <Badge variant="secondary">{item.action}</Badge>
                          <Badge variant="outline">置信度 {item.confidence}</Badge>
                        </div>
                        <p className="mt-3 text-sm">{item.summary}</p>
                        <div className="mt-3 flex flex-wrap gap-2 text-muted-foreground text-xs">
                          {item.theme_name ? <span>题材 {item.theme_name}</span> : null}
                          {item.role_label ? <span>角色 {item.role_label}</span> : null}
                          {item.trend_quality ? <span>趋势 {item.trend_quality}</span> : null}
                          {item.tradeability_state ? <span>{item.tradeability_state}</span> : null}
                        </div>
                        <p className="mt-3 text-muted-foreground text-sm">{item.observation_window}</p>
                        <p className="mt-2 text-muted-foreground text-sm">{item.position_hint}</p>
                        {item.invalid_conditions[0] ? (
                          <p className="mt-3 text-muted-foreground text-sm">
                            失效条件：{item.invalid_conditions[0]}
                          </p>
                        ) : null}
                        {item.risk_controls[0] ? (
                          <p className="mt-2 text-muted-foreground text-sm">
                            风险提示：{item.risk_controls[0]}
                          </p>
                        ) : null}
                        <div className="mt-4 flex flex-wrap gap-2">
                          <Button size="sm" variant="outline" onClick={() => setSelectedHolding(item)}>
                            查看持仓裁决
                          </Button>
                          <Button asChild size="sm" variant="outline">
                            <Link to="/home/exit-risk-center">去卖点与风险中心</Link>
                          </Button>
                          <Button asChild size="sm" variant="outline">
                            <Link to="/home/daily-review">去复盘记录</Link>
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                    当前阶段暂无持仓，继续保持保守观察。
                  </div>
                )}
              </section>
            ))}
          </div>
        </>
      ) : null}

      <HoldingExitSignalPreviewDialog
        holding={selectedHolding}
        open={!!selectedHolding}
        onOpenChange={(open) => {
          if (!open) setSelectedHolding(null);
        }}
      />
    </div>
  );
}
