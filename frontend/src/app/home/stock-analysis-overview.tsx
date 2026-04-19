import BackButton from "@valuecell/button/back-button";
import { Link } from "react-router";
import { useGetStockAnalysisOverview } from "@/api/stock-analysis-overview";
import { StockAnalysisActionQueue } from "@/app/home/components/stock-analysis-action-queue";
import { StockAnalysisOverviewSummary } from "@/app/home/components/stock-analysis-overview-summary";
import { StockAnalysisQualitySummary } from "@/app/home/components/stock-analysis-quality-summary";
import { StockAnalysisThreadOverviewCard } from "@/app/home/components/stock-analysis-thread-overview-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

export default function StockAnalysisOverviewPage() {
  const { data, isLoading, isError } = useGetStockAnalysisOverview();

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-semibold text-2xl">股票研究总览</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            先看最值得优先处理的线程、冲突、refresh 与高优任务，再进入具体线程继续研究。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to="/home/stock-analysis">进入线程工作区</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/home/daily-workbench">回到总控台</Link>
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex min-h-72 items-center justify-center">
          <Spinner className="size-6" />
        </div>
      ) : null}

      {!isLoading && (isError || !data) ? (
        <div className="rounded-xl border border-dashed p-6 text-muted-foreground text-sm">
          当前无法加载股票研究总览，请稍后再试。
        </div>
      ) : null}

      {!isLoading && !isError && data ? (
        <>
          {data.available ? (
            <>
              <StockAnalysisOverviewSummary overview={data} />

              <StockAnalysisActionQueue items={data.action_queue} />

              <div className="grid gap-4 xl:grid-cols-2">
                <div className="rounded-2xl border bg-background p-5">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-medium text-base">高冲突线程</p>
                      <p className="mt-1 text-muted-foreground text-sm">
                        当前 thesis 冲突最高、需要先回看 conflict summary 的线程。
                      </p>
                    </div>
                    <Badge variant="secondary">{data.high_conflict_threads.length}</Badge>
                  </div>
                  <div className="mt-4 space-y-3">
                    {data.high_conflict_threads.length ? (
                      data.high_conflict_threads.map((item) => (
                        <StockAnalysisThreadOverviewCard
                          key={`conflict-${item.thread_id}`}
                          item={item}
                        />
                      ))
                    ) : (
                      <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                        当前没有显式 high conflict 线程。
                      </div>
                    )}
                  </div>
                </div>

                <div className="rounded-2xl border bg-background p-5">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-medium text-base">需 Refresh 线程</p>
                      <p className="mt-1 text-muted-foreground text-sm">
                        优先处理 stale context 与 refresh recommended 信号。
                      </p>
                    </div>
                    <Badge variant="secondary">{data.refresh_needed_threads.length}</Badge>
                  </div>
                  <div className="mt-4 space-y-3">
                    {data.refresh_needed_threads.length ? (
                      data.refresh_needed_threads.map((item) => (
                        <StockAnalysisThreadOverviewCard
                          key={`refresh-${item.thread_id}`}
                          item={item}
                        />
                      ))
                    ) : (
                      <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                        当前没有明显需要优先 refresh 的线程。
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border bg-background p-5">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-base">高优先级 Tasks</p>
                    <p className="mt-1 text-muted-foreground text-sm">
                      这里只保留最重要的摘要，不复制完整 task center。
                    </p>
                  </div>
                  <Badge variant="secondary">{data.high_priority_tasks.length}</Badge>
                </div>
                <div className="mt-4 grid gap-3 xl:grid-cols-2">
                  {data.high_priority_tasks.length ? (
                    data.high_priority_tasks.map((task) => (
                      <div key={task.task_id} className="rounded-xl border p-4">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant="secondary">{task.priority}</Badge>
                          <Badge variant="outline">{task.task_type}</Badge>
                          <Badge variant="outline">{task.thread_title}</Badge>
                        </div>
                        <p className="mt-3 font-medium text-sm">{task.title}</p>
                        <p className="mt-1 text-muted-foreground text-sm">{task.summary}</p>
                        <p className="mt-2 text-sm">{task.reason || "回到线程后继续处理该任务。"}</p>
                        <div className="mt-3">
                          <Button asChild size="sm" variant="outline">
                            <Link to={`/home/stock-analysis?threadId=${task.thread_id}`}>
                              回到线程处理
                            </Link>
                          </Button>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                      当前没有高优先级任务堆积。
                    </div>
                  )}
                </div>
              </div>

              <StockAnalysisQualitySummary overview={data} />

              <div className="rounded-2xl border bg-background p-5">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-base">全部线程总览</p>
                    <p className="mt-1 text-muted-foreground text-sm">
                      按 thread health 与优先级排序，先展示更值得先看的线程。
                    </p>
                  </div>
                  <Badge variant="secondary">{data.thread_overview_items.length}</Badge>
                </div>
                <div className="mt-4 grid gap-4 xl:grid-cols-2">
                  {data.thread_overview_items.map((item) => (
                    <StockAnalysisThreadOverviewCard
                      key={`thread-${item.thread_id}`}
                      item={item}
                    />
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="rounded-xl border border-dashed p-6 text-muted-foreground text-sm">
              {data.empty_message || "当前还没有可展示的股票研究线程。"}
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
