import BackButton from "@valuecell/button/back-button";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router";
import {
  useGetAShareDailySnapshotDetail,
  useGetAShareDailySnapshots,
  useRefreshAShareDailySnapshot,
} from "@/api/ashare-daily-snapshot";
import { useGetDecisionEffectivenessSummary } from "@/api/decision-effectiveness";
import { useCaptureDecisionRecords, useRefreshDecisionRecords } from "@/api/decision-record";
import DailyReviewDecisionRecords from "@/app/home/components/daily-review-decision-records";
import DailyReviewDetailPanel from "@/app/home/components/daily-review-detail-panel";
import DailyReviewSummaryPanel from "@/app/home/components/daily-review-summary-panel";
import DailyReviewTimeline from "@/app/home/components/daily-review-timeline";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

export default function DailyReview() {
  const { data: snapshots, isLoading, isError } = useGetAShareDailySnapshots({
    limit: 14,
    includeToday: true,
  });
  const refreshSnapshot = useRefreshAShareDailySnapshot();
  const captureDecisionRecords = useCaptureDecisionRecords();
  const refreshDecisionRecords = useRefreshDecisionRecords();
  const { data: effectivenessSummary } = useGetDecisionEffectivenessSummary();
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const { data: snapshotDetail, isLoading: detailLoading } =
    useGetAShareDailySnapshotDetail(selectedDate, !!selectedDate);

  useEffect(() => {
    if (!selectedDate && snapshots?.items.length) {
      setSelectedDate(snapshots.items[0].snapshot_date);
    }
  }, [selectedDate, snapshots?.items]);

  const currentSnapshot = snapshots?.items[0] || null;
  const previousSnapshot = snapshots?.items[1] || null;

  const reviewTone = useMemo(() => {
    if (!currentSnapshot) return "值得继续观察";
    const riskCount = currentSnapshot.attention_digest.risk_alert_count || 0;
    const holdingRiskCount = currentSnapshot.attention_digest.holding_risk_count || 0;
    const nearEntryCount = currentSnapshot.attention_digest.near_entry_count || 0;
    if (riskCount >= 2 || holdingRiskCount >= 2) return "风险偏强";
    if (nearEntryCount > ((previousSnapshot?.attention_digest.near_entry_count || 0))) {
      return "机会改善";
    }
    return "偏防守";
  }, [currentSnapshot, previousSnapshot]);

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-semibold text-2xl">A 股复盘中心</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            复盘市场、机会、提醒和持仓处理的日级变化，不构成交易指令。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            onClick={() => refreshSnapshot.mutate()}
            disabled={refreshSnapshot.isPending}
          >
            {refreshSnapshot.isPending ? "记录中..." : "记录今日快照"}
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/daily-workbench">返回总控台</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/opportunities">去机会池</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/alerts">去提醒中心</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/theme-radar">去题材雷达</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/watchlist-center">去观察池中心</Link>
          </Button>
          <Button
            variant="outline"
            onClick={() => captureDecisionRecords.mutate()}
            disabled={captureDecisionRecords.isPending}
          >
            {captureDecisionRecords.isPending ? "沉淀中..." : "沉淀关键记录"}
          </Button>
          <Button
            variant="outline"
            onClick={() => refreshDecisionRecords.mutate()}
            disabled={refreshDecisionRecords.isPending}
          >
            {refreshDecisionRecords.isPending ? "刷新中..." : "刷新决策记录"}
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/holding-lifecycle">去持仓周期中心</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/exit-risk-center">去卖点与风险中心</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/decision-reviews">查看全部决策结果回看</Link>
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex min-h-72 items-center justify-center">
          <Spinner className="size-6" />
        </div>
      ) : null}

      {!isLoading && (isError || !snapshots?.items.length) ? (
        <div className="rounded-xl border border-dashed p-6 text-muted-foreground text-sm">
          暂无可用日级快照，请先记录今日快照。
        </div>
      ) : null}

      {!isLoading && !isError && snapshots?.items.length ? (
        <>
          <section className="rounded-2xl border bg-background p-5">
            <p className="font-semibold text-lg">复盘口径</p>
            <p className="mt-2 text-muted-foreground text-sm">
              当前复盘口径：{reviewTone}。关注风险回避、接近可参与窗口和持仓处理动作的日级变化。
            </p>
          </section>

          {effectivenessSummary?.available ? (
            <section className="rounded-2xl border bg-background p-5">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <p className="font-semibold text-lg">近期决策有效性摘要</p>
                  <p className="mt-2 text-muted-foreground text-sm">
                    {effectivenessSummary.overall_summary}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full bg-secondary px-3 py-1 text-sm">
                    总体得分 {effectivenessSummary.overall_score}
                  </span>
                  <span className="rounded-full border px-3 py-1 text-sm">
                    有效 {effectivenessSummary.effective_count}
                  </span>
                  <span className="rounded-full border px-3 py-1 text-sm">
                    失效 {effectivenessSummary.failed_count}
                  </span>
                </div>
              </div>
            </section>
          ) : null}

          <DailyReviewSummaryPanel
            current={currentSnapshot}
            previous={previousSnapshot}
          />

          <div className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <DailyReviewTimeline
              items={snapshots.items}
              selectedDate={selectedDate}
              onSelect={setSelectedDate}
            />
            {detailLoading ? (
              <div className="flex min-h-64 items-center justify-center rounded-2xl border bg-background">
                <Spinner className="size-5" />
              </div>
            ) : (
              <DailyReviewDetailPanel snapshot={snapshotDetail || null} />
            )}
          </div>

          <DailyReviewDecisionRecords />
        </>
      ) : null}
    </div>
  );
}
