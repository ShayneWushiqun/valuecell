import { useMemo } from "react";
import { useGetEntryTimingSignals } from "@/api/entry-timing";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";

export default function EntryTimingSummaryPanel() {
  const {
    data: entryTimingSignals,
    isLoading,
    isError,
  } = useGetEntryTimingSignals();

  const topSignals = useMemo(
    () => (entryTimingSignals?.items || []).slice(0, 4),
    [entryTimingSignals?.items],
  );

  return (
    <div className="rounded-2xl border bg-background p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="font-medium text-base">买点裁决</h2>
          <p className="mt-1 text-muted-foreground text-sm">
            仅补充规则版观察结论，帮助区分等待确认、持有观察和风险回避。
          </p>
        </div>
        {isLoading ? <Spinner className="size-4" /> : null}
      </div>

      {!isLoading && (isError || !entryTimingSignals?.available || !topSignals.length) ? (
        <div className="mt-3 rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
          暂无买点裁决信号
        </div>
      ) : null}

      {!isLoading && !isError && topSignals.length ? (
        <div className="mt-3 grid gap-3 xl:grid-cols-2">
          {topSignals.map((signal) => (
            <div key={signal.ticker} className="rounded-xl border bg-card p-3">
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium text-sm">{signal.display_name}</p>
                <Badge variant="secondary">{signal.action}</Badge>
                <Badge variant="outline">置信度 {signal.confidence}</Badge>
              </div>
              <p className="mt-2 text-muted-foreground text-sm">{signal.summary}</p>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
