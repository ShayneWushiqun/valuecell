import BackButton from "@valuecell/button/back-button";
import { useMemo, useState } from "react";
import { Link } from "react-router";
import { useGetDecisionEffectivenessSummary } from "@/api/decision-effectiveness";
import { useGetDecisionOutcomeReviews } from "@/api/decision-outcome-review";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Spinner } from "@/components/ui/spinner";

const OUTCOME_FILTERS = ["全部", "有效", "部分有效", "失效", "仍在观察", "数据不足"] as const;
const ACTION_FILTERS = [
  "全部",
  "继续持有",
  "持有观察",
  "减仓观察",
  "保护利润",
  "纪律止损",
] as const;
const HORIZON_FILTERS = [5, 10, 20] as const;

const formatPct = (value: number | null) => {
  if (value === null || Number.isNaN(value)) return "--";
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}%`;
};

const getOutcomeTone = (status: string) => {
  if (status === "有效") return "bg-emerald-500/10 text-emerald-600";
  if (status === "部分有效") return "bg-blue-500/10 text-blue-600";
  if (status === "失效") return "bg-amber-500/10 text-amber-600";
  if (status === "仍在观察") return "bg-slate-500/10 text-slate-600";
  return "bg-muted text-muted-foreground";
};

export default function DecisionReviews() {
  const [activeOutcome, setActiveOutcome] =
    useState<(typeof OUTCOME_FILTERS)[number]>("全部");
  const [activeAction, setActiveAction] =
    useState<(typeof ACTION_FILTERS)[number]>("全部");
  const [activeHorizon, setActiveHorizon] =
    useState<(typeof HORIZON_FILTERS)[number]>(10);

  const outcomeStatus = activeOutcome === "全部" ? undefined : activeOutcome;
  const action = activeAction === "全部" ? undefined : activeAction;

  const {
    data: effectivenessSummary,
    isLoading: effectivenessLoading,
    isError: effectivenessError,
  } = useGetDecisionEffectivenessSummary();
  const {
    data: reviews,
    isLoading: reviewsLoading,
    isError: reviewsError,
  } = useGetDecisionOutcomeReviews({
    limit: 120,
    outcomeStatus,
    action,
    reviewHorizonDays: activeHorizon,
  });

  const topCounts = useMemo(
    () => [
      { label: "回看总数", value: effectivenessSummary?.review_count ?? 0 },
      { label: "有效", value: effectivenessSummary?.effective_count ?? 0 },
      {
        label: "部分有效",
        value: effectivenessSummary?.partially_effective_count ?? 0,
      },
      { label: "失效", value: effectivenessSummary?.failed_count ?? 0 },
      { label: "仍在观察", value: effectivenessSummary?.observing_count ?? 0 },
      {
        label: "数据不足",
        value: effectivenessSummary?.insufficient_count ?? 0,
      },
    ],
    [effectivenessSummary],
  );

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-semibold text-2xl">决策结果回看</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            系统查看最近 outcome review，判断哪些动作更稳，哪些动作需要继续收紧节奏。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to="/home/daily-review">去复盘中心</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/decision-contexts">去决策上下文页</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/risk-sizing">去风控分仓建议</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/daily-workbench">返回总控台</Link>
          </Button>
        </div>
      </div>

      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
        {topCounts.map((item) => (
          <Card key={item.label} className="gap-3 py-4">
            <CardHeader className="px-4">
              <CardDescription>{item.label}</CardDescription>
            </CardHeader>
            <CardContent className="px-4">
              <p className="font-semibold text-2xl">{item.value}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <Card>
          <CardHeader>
            <CardTitle>有效性摘要</CardTitle>
            <CardDescription>仅聚合最近 40 天已有回看，不重复重算结果判定。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {effectivenessLoading ? (
              <div className="flex min-h-40 items-center justify-center">
                <Spinner className="size-5" />
              </div>
            ) : effectivenessError || !effectivenessSummary?.available ? (
              <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                {effectivenessSummary?.empty_message || "暂无可用有效性摘要"}
              </div>
            ) : (
              <>
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-semibold text-xl">
                        总体得分 {effectivenessSummary.overall_score}
                      </p>
                      <p className="mt-1 text-muted-foreground text-sm">
                        {effectivenessSummary.overall_summary}
                      </p>
                    </div>
                    <Badge variant="secondary">{effectivenessSummary.review_count} 条样本</Badge>
                  </div>
                  <Progress value={effectivenessSummary.overall_score} />
                </div>
                <div className="grid gap-3 lg:grid-cols-2">
                  <div className="rounded-xl border p-4">
                    <p className="font-medium text-sm">动作拆分</p>
                    <div className="mt-3 space-y-2">
                      {effectivenessSummary.action_breakdown
                        .filter((item) => item.count > 0)
                        .map((item) => (
                          <div
                            key={item.label}
                            className="flex items-center justify-between text-sm"
                          >
                            <span>{item.label}</span>
                            <span className="text-muted-foreground">
                              {item.count} 条 / 均分 {item.average_score}
                            </span>
                          </div>
                        ))}
                    </div>
                  </div>
                  <div className="rounded-xl border p-4">
                    <p className="font-medium text-sm">高频题材</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {effectivenessSummary.theme_breakdown.length ? (
                        effectivenessSummary.theme_breakdown.map((item) => (
                          <Badge key={item.label} variant="outline">
                            {item.label} · {item.count}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-muted-foreground text-sm">
                          暂无足够题材样本
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>最近样本</CardTitle>
            <CardDescription>用于前端快速判断近期哪些动作更靠谱。</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-1">
            <div className="rounded-xl border p-4">
              <p className="font-medium text-sm">最近成功</p>
              <div className="mt-3 space-y-3">
                {effectivenessSummary?.recent_successes.length ? (
                  effectivenessSummary.recent_successes.map((item) => (
                    <div key={`${item.ticker}-${item.review_date}`} className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{item.display_name}</span>
                        <Badge variant="outline">{item.action}</Badge>
                      </div>
                      <p className="text-muted-foreground text-xs">{item.summary}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground text-sm">暂无近期成功样本</p>
                )}
              </div>
            </div>
            <div className="rounded-xl border p-4">
              <p className="font-medium text-sm">最近失配</p>
              <div className="mt-3 space-y-3">
                {effectivenessSummary?.recent_failures.length ? (
                  effectivenessSummary.recent_failures.map((item) => (
                    <div key={`${item.ticker}-${item.review_date}`} className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{item.display_name}</span>
                        <Badge variant="outline">{item.action}</Badge>
                      </div>
                      <p className="text-muted-foreground text-xs">{item.summary}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground text-sm">暂无近期失配样本</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>筛选</CardTitle>
          <CardDescription>按状态、动作和窗口查看最近回看，不把任何统计直接当成交易指令。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {OUTCOME_FILTERS.map((option) => (
              <Button
                key={option}
                size="sm"
                variant={activeOutcome === option ? "default" : "outline"}
                onClick={() => setActiveOutcome(option)}
              >
                {option}
              </Button>
            ))}
          </div>
          <div className="flex flex-wrap gap-2">
            {ACTION_FILTERS.map((option) => (
              <Button
                key={option}
                size="sm"
                variant={activeAction === option ? "default" : "outline"}
                onClick={() => setActiveAction(option)}
              >
                {option}
              </Button>
            ))}
          </div>
          <div className="flex flex-wrap gap-2">
            {HORIZON_FILTERS.map((option) => (
              <Button
                key={option}
                size="sm"
                variant={activeHorizon === option ? "default" : "outline"}
                onClick={() => setActiveHorizon(option)}
              >
                {option} 日窗口
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {reviewsLoading ? (
        <div className="flex min-h-72 items-center justify-center">
          <Spinner className="size-6" />
        </div>
      ) : null}

      {!reviewsLoading && (reviewsError || !reviews?.items.length) ? (
        <div className="rounded-xl border border-dashed p-6 text-muted-foreground text-sm">
          当前筛选下暂无可用回看结果，先保持轻量观察。
        </div>
      ) : null}

      {!reviewsLoading && !reviewsError && reviews?.items.length ? (
        <div className="space-y-4">
          {reviews.items.map((item) => (
            <Card key={item.review_id}>
              <CardHeader className="gap-3">
                <div className="flex flex-wrap items-center gap-2">
                  <CardTitle>{item.display_name}</CardTitle>
                  <Badge variant="outline">{item.ticker}</Badge>
                  <Badge variant="secondary">{item.action}</Badge>
                  <Badge className={getOutcomeTone(item.outcome_status)}>
                    {item.outcome_status}
                  </Badge>
                  <Badge variant="outline">评分 {item.outcome_score}</Badge>
                  <Badge variant="outline">{item.review_horizon_days} 日</Badge>
                </div>
                <CardDescription>
                  记录日 {item.record_date} · 回看日 {item.review_date} ·
                  生命周期 {item.lifecycle_stage || "待补充"}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm">{item.summary}</p>
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-xl border p-3">
                    <p className="text-muted-foreground text-xs">价格变化</p>
                    <p className="mt-2 font-medium text-sm">
                      {formatPct(item.price_change_pct)}
                    </p>
                  </div>
                  <div className="rounded-xl border p-3">
                    <p className="text-muted-foreground text-xs">最大有利波动</p>
                    <p className="mt-2 font-medium text-sm">
                      {formatPct(item.max_favorable_excursion_pct)}
                    </p>
                  </div>
                  <div className="rounded-xl border p-3">
                    <p className="text-muted-foreground text-xs">最大不利波动</p>
                    <p className="mt-2 font-medium text-sm">
                      {formatPct(item.max_adverse_excursion_pct)}
                    </p>
                  </div>
                </div>
                <div className="grid gap-3 lg:grid-cols-3">
                  <div className="rounded-xl border p-4">
                    <p className="font-medium text-sm">判断对的地方</p>
                    <p className="mt-2 text-muted-foreground text-sm">{item.what_was_right}</p>
                  </div>
                  <div className="rounded-xl border p-4">
                    <p className="font-medium text-sm">判断偏差</p>
                    <p className="mt-2 text-muted-foreground text-sm">{item.what_was_wrong}</p>
                  </div>
                  <div className="rounded-xl border p-4">
                    <p className="font-medium text-sm">后续视角</p>
                    <p className="mt-2 text-muted-foreground text-sm">{item.followup_view}</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button asChild size="sm" variant="outline">
                    <Link to="/home/daily-review">查看关联 decision record</Link>
                  </Button>
                  <Button asChild size="sm" variant="outline">
                    <Link to="/home/decision-contexts">查看关联 decision context</Link>
                  </Button>
                  {item.linked_context_window_id ? (
                    <Button asChild size="sm" variant="outline">
                      <Link to="/home/decision-contexts">
                        查看时间窗 #{item.linked_context_window_id}
                      </Link>
                    </Button>
                  ) : (
                    <div className="flex items-center text-muted-foreground text-xs">
                      暂无关联时间窗
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : null}
    </div>
  );
}
