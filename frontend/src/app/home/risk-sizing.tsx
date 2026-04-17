import BackButton from "@valuecell/button/back-button";
import { useEffect, useState } from "react";
import { Link } from "react-router";
import { useGetRiskSizingSummary, useGetRiskSizingTicker } from "@/api/risk-sizing";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";

const getRiskTone = (riskLevel: string) => {
  if (riskLevel === "高" || riskLevel === "偏高") return "bg-amber-500/10 text-amber-600";
  if (riskLevel === "中" || riskLevel === "中性") return "bg-blue-500/10 text-blue-600";
  return "bg-emerald-500/10 text-emerald-600";
};

export default function RiskSizing() {
  const { data, isLoading, isError } = useGetRiskSizingSummary();
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const { data: tickerDetail, isLoading: tickerLoading } = useGetRiskSizingTicker(
    selectedTicker,
    !!selectedTicker,
  );

  useEffect(() => {
    if (!selectedTicker && data?.ticker_suggestions.length) {
      setSelectedTicker(data.ticker_suggestions[0].ticker);
    }
  }, [selectedTicker, data?.ticker_suggestions]);

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-semibold text-2xl">风控分仓建议</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            把总仓位、单票仓位和加仓节奏单独收口成保守建议，不输出交易指令。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to="/home/daily-workbench">返回总控台</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/opportunities">去机会池</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/decision-reviews">去决策结果回看</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/holding-lifecycle">去持仓周期中心</Link>
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
          {data?.empty_message || "暂无可用风控分仓建议"}
        </div>
      ) : null}

      {!isLoading && !isError && data?.available ? (
        <>
          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <Card className="gap-3 py-4">
              <CardHeader className="px-4">
                <CardDescription>市场风险等级</CardDescription>
              </CardHeader>
              <CardContent className="px-4">
                <Badge className={getRiskTone(data.market_risk_level)}>
                  {data.market_risk_level}
                </Badge>
              </CardContent>
            </Card>
            <Card className="gap-3 py-4">
              <CardHeader className="px-4">
                <CardDescription>建议总仓位区间</CardDescription>
              </CardHeader>
              <CardContent className="px-4">
                <p className="font-semibold text-xl">{data.suggested_total_exposure_range}</p>
              </CardContent>
            </Card>
            <Card className="gap-3 py-4">
              <CardHeader className="px-4">
                <CardDescription>建议新开仓区间</CardDescription>
              </CardHeader>
              <CardContent className="px-4">
                <p className="font-semibold text-xl">{data.suggested_new_position_range}</p>
              </CardContent>
            </Card>
            <Card className="gap-3 py-4">
              <CardHeader className="px-4">
                <CardDescription>建议加仓区间</CardDescription>
              </CardHeader>
              <CardContent className="px-4">
                <p className="font-semibold text-xl">{data.suggested_add_position_range}</p>
              </CardContent>
            </Card>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>组合层建议</CardTitle>
                <CardDescription>先看组合压力，再看是否允许新开和加仓。</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3">
                <div className="rounded-xl border p-4">
                  <p className="font-medium text-sm">持仓风险</p>
                  <p className="mt-2 text-muted-foreground text-sm">{data.holding_risk_note}</p>
                </div>
                <div className="rounded-xl border p-4">
                  <p className="font-medium text-sm">入场风险</p>
                  <p className="mt-2 text-muted-foreground text-sm">{data.entry_risk_note}</p>
                </div>
                <div className="rounded-xl border p-4">
                  <p className="font-medium text-sm">组合平衡</p>
                  <p className="mt-2 text-muted-foreground text-sm">
                    {data.portfolio_balance_note}
                  </p>
                </div>
                <div className="rounded-xl border p-4">
                  <p className="font-medium text-sm">今日动作队列</p>
                  <p className="mt-2 text-muted-foreground text-sm">{data.action_queue_note}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>单票细化建议</CardTitle>
                <CardDescription>优先显示当前选中的重点 ticker，更方便比较核心票与弱票差异。</CardDescription>
              </CardHeader>
              <CardContent>
                {tickerLoading ? (
                  <div className="flex min-h-48 items-center justify-center">
                    <Spinner className="size-5" />
                  </div>
                ) : tickerDetail?.available ? (
                  <div className="space-y-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold text-lg">{tickerDetail.display_name}</p>
                      <Badge variant="outline">{tickerDetail.ticker}</Badge>
                      <Badge className={getRiskTone(tickerDetail.risk_level)}>
                        风险 {tickerDetail.risk_level}
                      </Badge>
                    </div>
                    <p className="text-sm">{tickerDetail.summary}</p>
                    <div className="grid gap-3 md:grid-cols-3">
                      <div className="rounded-xl border p-3">
                        <p className="text-muted-foreground text-xs">建议单票区间</p>
                        <p className="mt-2 font-medium text-sm">
                          {tickerDetail.suggested_position_range}
                        </p>
                      </div>
                      <div className="rounded-xl border p-3">
                        <p className="text-muted-foreground text-xs">首次参与区间</p>
                        <p className="mt-2 font-medium text-sm">
                          {tickerDetail.suggested_first_entry_range}
                        </p>
                      </div>
                      <div className="rounded-xl border p-3">
                        <p className="text-muted-foreground text-xs">加仓区间</p>
                        <p className="mt-2 font-medium text-sm">
                          {tickerDetail.suggested_add_range}
                        </p>
                      </div>
                    </div>
                    <div className="grid gap-3">
                      <div className="rounded-xl border p-4">
                        <p className="font-medium text-sm">止损风格</p>
                        <p className="mt-2 text-muted-foreground text-sm">
                          {tickerDetail.stop_loss_style}
                        </p>
                      </div>
                      <div className="rounded-xl border p-4">
                        <p className="font-medium text-sm">利润保护风格</p>
                        <p className="mt-2 text-muted-foreground text-sm">
                          {tickerDetail.profit_protection_style}
                        </p>
                      </div>
                      {tickerDetail.liquidity_warning ? (
                        <div className="rounded-xl border p-4">
                          <p className="font-medium text-sm">流动性提示</p>
                          <p className="mt-2 text-muted-foreground text-sm">
                            {tickerDetail.liquidity_warning}
                          </p>
                        </div>
                      ) : null}
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                    {tickerDetail?.empty_message || "当前未选中可用 ticker 建议"}
                  </div>
                )}
              </CardContent>
            </Card>
          </section>

          <Card>
            <CardHeader>
              <CardTitle>重点 ticker 建议</CardTitle>
              <CardDescription>
                优先从当前持仓、机会池前列和风险中心重点项里提取，帮助快速比较不同标的的仓位容忍度。
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 xl:grid-cols-2">
              {data.ticker_suggestions.map((item) => (
                <button
                  type="button"
                  key={item.ticker}
                  onClick={() => setSelectedTicker(item.ticker)}
                  className={`rounded-2xl border p-4 text-left transition ${
                    selectedTicker === item.ticker ? "border-primary bg-primary/5" : "bg-background"
                  }`}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold text-base">{item.display_name}</p>
                    <Badge variant="outline">{item.ticker}</Badge>
                    <Badge className={getRiskTone(item.risk_level)}>
                      风险 {item.risk_level}
                    </Badge>
                  </div>
                  <p className="mt-3 text-sm">{item.summary}</p>
                  <div className="mt-3 grid gap-2 text-muted-foreground text-xs md:grid-cols-3">
                    <span>单票 {item.suggested_position_range}</span>
                    <span>首笔 {item.suggested_first_entry_range}</span>
                    <span>加仓 {item.suggested_add_range}</span>
                  </div>
                  {item.liquidity_warning ? (
                    <p className="mt-3 text-muted-foreground text-xs">{item.liquidity_warning}</p>
                  ) : null}
                  <div className="mt-3 flex flex-wrap gap-2">
                    {item.reasons.map((reason) => (
                      <Badge key={reason} variant="secondary" className="whitespace-normal">
                        {reason}
                      </Badge>
                    ))}
                  </div>
                </button>
              ))}
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}
