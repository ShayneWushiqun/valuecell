import BackButton from "@valuecell/button/back-button";
import { Link } from "react-router";
import { useGetExitRiskCenterOverview, useRefreshExitRiskCenter } from "@/api/exit-risk-center";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import type { ExitRiskItem } from "@/types/exit-risk-center";

const renderRiskGroup = (title: string, items: ExitRiskItem[]) => (
  <section className="space-y-3">
    <div className="flex items-center justify-between">
      <p className="font-semibold text-lg">{title}</p>
      <Badge variant="outline">{items.length} 项</Badge>
    </div>
    {items.length ? (
      <div className="grid gap-4 xl:grid-cols-2">
        {items.map((item) => (
          <div key={`${title}-${item.holding_id}`} className="rounded-2xl border bg-background p-4">
            <div className="flex flex-wrap items-center gap-2">
              <p className="font-semibold text-base">{item.display_name}</p>
              <Badge variant="outline">{item.ticker}</Badge>
              <Badge variant="secondary">{item.action}</Badge>
              <Badge variant="outline">{item.risk_type}</Badge>
              <Badge variant="outline">置信度 {item.confidence}</Badge>
            </div>
            <p className="mt-3 text-sm">{item.summary}</p>
            <p className="mt-2 text-muted-foreground text-sm">{item.thesis}</p>
            <div className="mt-3 space-y-1 text-muted-foreground text-sm">
              {item.evidence.slice(0, 3).map((evidence) => (
                <p key={`${item.holding_id}-${evidence}`}>- {evidence}</p>
              ))}
            </div>
            {item.disagreement[0] ? (
              <p className="mt-3 text-muted-foreground text-sm">矛盾点：{item.disagreement[0]}</p>
            ) : null}
            {item.invalid_conditions[0] ? (
              <p className="mt-2 text-muted-foreground text-sm">
                失效条件：{item.invalid_conditions[0]}
              </p>
            ) : null}
            {item.risk_controls[0] ? (
              <p className="mt-2 text-muted-foreground text-sm">风控提示：{item.risk_controls[0]}</p>
            ) : null}
            {item.liquidity_warning ? (
              <p className="mt-2 text-muted-foreground text-sm">退出难度：{item.liquidity_warning}</p>
            ) : null}
            <p className="mt-2 text-muted-foreground text-sm">退出计划：{item.expected_exit_plan}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Button asChild size="sm" variant="outline">
                <Link to={`/home/decision-contexts?ticker=${encodeURIComponent(item.ticker)}`}>
                  查看决策上下文
                </Link>
              </Button>
            </div>
          </div>
        ))}
      </div>
    ) : (
      <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
        当前分组暂无持仓项。
      </div>
    )}
  </section>
);

export default function ExitRiskCenter() {
  const { data, isLoading, isError } = useGetExitRiskCenterOverview();
  const refresh = useRefreshExitRiskCenter();

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-semibold text-2xl">卖点与风险中心</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            把今天优先处理的持仓集中展示，先看风险与退出难度，再看动作节奏。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => refresh.mutate()} disabled={refresh.isPending}>
            {refresh.isPending ? "刷新中..." : "刷新风险中心"}
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/holding-lifecycle">去持仓周期中心</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/daily-review">去复盘中心</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/daily-workbench">返回总控台</Link>
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
          {data?.empty_message || "暂无可用卖点与风险中心数据"}
        </div>
      ) : null}

      {!isLoading && !isError && data?.available ? (
        <>
          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border bg-background p-4">
              <p className="text-muted-foreground text-sm">高优先级处理</p>
              <p className="mt-2 font-semibold text-2xl">{data.high_priority_items.length}</p>
            </div>
            <div className="rounded-2xl border bg-background p-4">
              <p className="text-muted-foreground text-sm">保护利润</p>
              <p className="mt-2 font-semibold text-2xl">{data.profit_protection_items.length}</p>
            </div>
            <div className="rounded-2xl border bg-background p-4">
              <p className="text-muted-foreground text-sm">纪律止损</p>
              <p className="mt-2 font-semibold text-2xl">{data.discipline_stop_items.length}</p>
            </div>
            <div className="rounded-2xl border bg-background p-4">
              <p className="text-muted-foreground text-sm">继续观察</p>
              <p className="mt-2 font-semibold text-2xl">{data.watch_items.length}</p>
            </div>
          </section>

          <section className="rounded-2xl border bg-background p-4">
            <div className="flex flex-wrap gap-2 text-sm">
              {Object.entries(data.risk_buckets).map(([riskType, count]) => (
                <Badge key={riskType} variant="outline">
                  {riskType} {count}
                </Badge>
              ))}
            </div>
          </section>

          {renderRiskGroup("今日高优先级处理", data.high_priority_items)}
          {renderRiskGroup("保护利润", data.profit_protection_items)}
          {renderRiskGroup("纪律止损", data.discipline_stop_items)}
          {renderRiskGroup("继续观察", data.watch_items)}
        </>
      ) : null}
    </div>
  );
}
