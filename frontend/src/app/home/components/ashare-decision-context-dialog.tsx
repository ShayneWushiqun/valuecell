import { useState } from "react";
import { useGetAShareDecisionContext } from "@/api/ashare-decision-context";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Spinner } from "@/components/ui/spinner";

export default function AShareDecisionContextDialog({
  ticker,
  displayName,
}: {
  ticker: string;
  displayName: string;
}) {
  const [open, setOpen] = useState(false);
  const { data, isLoading, isError } = useGetAShareDecisionContext(ticker, open);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          查看裁决上下文
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>{displayName} 深度分析上下文</DialogTitle>
          <DialogDescription>
            这里只展示规则版裁决上下文与 Agent prompt 预览，不构成买入指令。
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex min-h-40 items-center justify-center">
            <Spinner className="size-5" />
          </div>
        ) : null}

        {!isLoading && (isError || !data?.available) ? (
          <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
            {data?.empty_message || "暂无可用裁决上下文"}
          </div>
        ) : null}

        {!isLoading && !isError && data?.available ? (
          <div className="space-y-4">
            <section className="rounded-xl border bg-card p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="secondary">{data.rule_based_judgement.action}</Badge>
                {data.entry_timing_context.confidence !== null ? (
                  <Badge variant="outline">
                    置信度 {data.entry_timing_context.confidence}
                  </Badge>
                ) : null}
              </div>
              <p className="mt-3 text-sm">{data.rule_based_judgement.summary}</p>
            </section>

            <section className="rounded-xl border bg-card p-4">
              <h3 className="font-medium text-sm">核心理由</h3>
              <div className="mt-2 space-y-1 text-muted-foreground text-sm">
                {data.rule_based_judgement.reasons.length ? (
                  data.rule_based_judgement.reasons.slice(0, 3).map((reason) => (
                    <p key={reason}>- {reason}</p>
                  ))
                ) : (
                  <p>- 当前暂无额外理由，仍需继续观察。</p>
                )}
              </div>
            </section>

            <section className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-xl border bg-card p-4">
                <h3 className="font-medium text-sm">缺失信息</h3>
                <div className="mt-2 space-y-1 text-muted-foreground text-sm">
                  {data.missing_context.length ? (
                    data.missing_context.map((item) => <p key={item}>- {item}</p>)
                  ) : (
                    <p>- 当前上下文较完整，但仍需要进一步确认。</p>
                  )}
                </div>
              </div>

              <div className="rounded-xl border bg-card p-4">
                <h3 className="font-medium text-sm">风险条件</h3>
                <div className="mt-2 space-y-1 text-muted-foreground text-sm">
                  {data.risk_context.items.length ? (
                    data.risk_context.items.slice(0, 5).map((item) => (
                      <p key={item}>- {item}</p>
                    ))
                  ) : (
                    <p>- 当前暂无额外风险条件，仍需保持保守观察。</p>
                  )}
                </div>
              </div>
            </section>

            <section className="rounded-xl border bg-card p-4">
              <h3 className="font-medium text-sm">Agent Prompt Preview</h3>
              <pre className="mt-2 whitespace-pre-wrap break-words text-muted-foreground text-sm">
                {data.agent_prompt_preview}
              </pre>
            </section>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
