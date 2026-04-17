import { useMemo, useState } from "react";
import { Link } from "react-router";
import { useGetDecisionRecords } from "@/api/decision-record";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import type { DecisionRecord } from "@/types/decision-record";

const FILTER_OPTIONS = [
  "全部",
  "继续持有",
  "持有观察",
  "减仓观察",
  "保护利润",
  "纪律止损",
] as const;

type DecisionFilter = (typeof FILTER_OPTIONS)[number];

const pickEvidence = (record: DecisionRecord) => record.evidence.slice(0, 2);

export default function DailyReviewDecisionRecords() {
  const [filter, setFilter] = useState<DecisionFilter>("全部");
  const { data, isLoading, isError } = useGetDecisionRecords({ limit: 20 });

  const filteredItems = useMemo(() => {
    if (filter === "全部") return data?.items || [];
    return (data?.items || []).filter((item) => item.action === filter);
  }, [data?.items, filter]);

  return (
    <section className="rounded-2xl border bg-background p-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="font-semibold text-lg">关键决策记录</p>
          <p className="mt-1 text-muted-foreground text-sm">
            回看当时为什么给出持仓处理判断，为后续复盘补齐依据。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {FILTER_OPTIONS.map((option) => (
            <Button
              key={option}
              size="sm"
              variant={filter === option ? "default" : "outline"}
              onClick={() => setFilter(option)}
            >
              {option}
            </Button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex min-h-36 items-center justify-center">
          <Spinner className="size-5" />
        </div>
      ) : null}

      {!isLoading && (isError || !data?.count) ? (
        <div className="mt-4 rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
          暂无可用决策记录，请先触发记录沉淀后再回看。
        </div>
      ) : null}

      {!isLoading && !isError && !!data?.count ? (
        <div className="mt-4 grid gap-3 xl:grid-cols-2">
          {filteredItems.length ? (
            filteredItems.map((item) => (
              <div key={item.record_id} className="rounded-xl border bg-card p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-medium text-sm">{item.display_name}</p>
                  <Badge variant="outline">{item.record_date}</Badge>
                  <Badge variant="secondary">{item.lifecycle_stage}</Badge>
                  <Badge variant="outline">{item.action}</Badge>
                </div>
                <p className="mt-3 text-sm">{item.summary}</p>
                <div className="mt-3 space-y-1 text-muted-foreground text-sm">
                  {pickEvidence(item).map((evidence) => (
                    <p key={`${item.record_id}-${evidence}`}>- {evidence}</p>
                  ))}
                </div>
                {item.invalid_conditions[0] ? (
                  <p className="mt-3 text-muted-foreground text-sm">
                    失效条件：{item.invalid_conditions[0]}
                  </p>
                ) : item.risk_controls[0] ? (
                  <p className="mt-3 text-muted-foreground text-sm">
                    风险提示：{item.risk_controls[0]}
                  </p>
                ) : null}
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button asChild size="sm" variant="outline">
                    <Link to={`/home/decision-contexts?ticker=${encodeURIComponent(item.ticker)}`}>
                      查看决策上下文
                    </Link>
                  </Button>
                  {item.context_window_id ? (
                    <Button asChild size="sm" variant="outline">
                      <Link
                        to={`/home/decision-contexts?ticker=${encodeURIComponent(item.ticker)}&windowId=${item.context_window_id}`}
                      >
                        查看对应时间窗
                      </Link>
                    </Button>
                  ) : null}
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
              当前筛选下暂无记录，先保持保守观察。
            </div>
          )}
        </div>
      ) : null}
    </section>
  );
}
