import BackButton from "@valuecell/button/back-button";
import { Link } from "react-router";
import { useGetAShareDailyWorkbenchOverview, useRefreshAShareDailyWorkbench } from "@/api/ashare-daily-workbench";
import DailyWorkbenchActionQueue from "@/app/home/components/daily-workbench-action-queue";
import DailyWorkbenchAlertPanel from "@/app/home/components/daily-workbench-alert-panel";
import DailyWorkbenchHoldingPanel from "@/app/home/components/daily-workbench-holding-panel";
import DailyWorkbenchMarketPanel from "@/app/home/components/daily-workbench-market-panel";
import DailyWorkbenchOpportunityPanel from "@/app/home/components/daily-workbench-opportunity-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

export default function DailyWorkbench() {
  const { data, isLoading, isError } = useGetAShareDailyWorkbenchOverview();
  const refreshWorkbench = useRefreshAShareDailyWorkbench();

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-semibold text-2xl">A 股每日决策总控台</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            先看风险，再看持仓，再看机会，不把任何摘要当成直接交易指令。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            onClick={() => refreshWorkbench.mutate()}
            disabled={refreshWorkbench.isPending}
          >
            {refreshWorkbench.isPending ? "刷新中..." : "刷新总控台"}
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/opportunities">去机会池</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/alerts">去提醒中心</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/daily-review">去复盘中心</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/theme-radar">去题材雷达</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/watchlist-center">去观察池中心</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/strategy-preferences">去策略偏好</Link>
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
          {data?.empty_message || "暂无可用总控台摘要"}
        </div>
      ) : null}

      {!isLoading && !isError && data?.available ? (
        <>
          <DailyWorkbenchMarketPanel marketDigest={data.market_digest} />

          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            <div className="rounded-2xl border bg-background p-4">
              <p className="text-muted-foreground text-sm">未读提醒</p>
              <p className="mt-2 font-semibold text-2xl">
                {data.attention_digest.unread_alert_count}
              </p>
            </div>
            <div className="rounded-2xl border bg-background p-4">
              <p className="text-muted-foreground text-sm">风险回避</p>
              <p className="mt-2 font-semibold text-2xl">
                {data.attention_digest.risk_alert_count}
              </p>
            </div>
            <div className="rounded-2xl border bg-background p-4">
              <p className="text-muted-foreground text-sm">接近可参与窗口</p>
              <p className="mt-2 font-semibold text-2xl">
                {data.attention_digest.near_entry_count}
              </p>
            </div>
            <div className="rounded-2xl border bg-background p-4">
              <p className="text-muted-foreground text-sm">需要处理的持仓</p>
              <p className="mt-2 font-semibold text-2xl">
                {data.attention_digest.holding_risk_count}
              </p>
            </div>
            <div className="rounded-2xl border bg-background p-4">
              <p className="text-muted-foreground text-sm">保护利润中的持仓</p>
              <p className="mt-2 font-semibold text-2xl">
                {data.attention_digest.holding_profit_protection_count}
              </p>
            </div>
          </section>

          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">风险优先</Badge>
            <Badge variant="outline">持仓优先于冲动追新</Badge>
            <Badge variant="outline">不构成交易指令</Badge>
          </div>

          <DailyWorkbenchActionQueue items={data.today_action_queue} />
          <DailyWorkbenchAlertPanel alerts={data.top_alerts} />
          <DailyWorkbenchOpportunityPanel opportunities={data.top_opportunities} />
          <DailyWorkbenchHoldingPanel
            toHandle={data.top_holdings_to_handle}
            stable={data.top_holdings_stable}
          />
        </>
      ) : null}
    </div>
  );
}
