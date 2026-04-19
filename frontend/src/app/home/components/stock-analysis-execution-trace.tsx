import { Badge } from "@/components/ui/badge";

type ExecutionStep = {
  step_id?: string;
  step_type?: string;
  title?: string;
  reason?: string;
  result_summary?: string | null;
};

type StockAnalysisExecutionTraceProps = {
  questionIntent?: string | null;
  responseStrategy?: string | null;
  executionPlanSummary?: string | null;
  executedSteps: Array<Record<string, unknown>>;
  skippedSteps: Array<Record<string, unknown>>;
  failedSteps: Array<Record<string, unknown>>;
};

const coerceSteps = (value: Array<Record<string, unknown>>) =>
  value.map((item) => item as ExecutionStep);

export function StockAnalysisExecutionTrace({
  questionIntent,
  responseStrategy,
  executionPlanSummary,
  executedSteps,
  skippedSteps,
  failedSteps,
}: StockAnalysisExecutionTraceProps) {
  if (
    !questionIntent &&
    !responseStrategy &&
    !executionPlanSummary &&
    !executedSteps.length &&
    !skippedSteps.length &&
    !failedSteps.length
  ) {
    return null;
  }

  const executed = coerceSteps(executedSteps);
  const skipped = coerceSteps(skippedSteps);
  const failed = coerceSteps(failedSteps);

  return (
    <div className="rounded-lg border border-dashed p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-medium">本轮研究路径</p>
        {questionIntent ? <Badge variant="secondary">{questionIntent}</Badge> : null}
        {responseStrategy ? <Badge variant="outline">{responseStrategy}</Badge> : null}
      </div>
      {executionPlanSummary ? (
        <p className="mt-2 text-muted-foreground">{executionPlanSummary}</p>
      ) : null}
      {executed.length ? (
        <div className="mt-3">
          <p className="font-medium text-foreground">已执行步骤</p>
          <div className="mt-2 space-y-2">
            {executed.map((step) => (
              <div key={step.step_id || step.step_type} className="rounded border p-2">
                <p>{step.title || step.step_type}</p>
                {step.result_summary ? (
                  <p className="mt-1 text-muted-foreground text-xs">{step.result_summary}</p>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
      {skipped.length ? (
        <div className="mt-3">
          <p className="font-medium text-foreground">跳过步骤</p>
          <div className="mt-2 space-y-2">
            {skipped.map((step) => (
              <div key={step.step_id || step.step_type} className="rounded border p-2">
                <p>{step.title || step.step_type}</p>
                {step.result_summary ? (
                  <p className="mt-1 text-muted-foreground text-xs">{step.result_summary}</p>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
      {failed.length ? (
        <div className="mt-3">
          <p className="font-medium text-foreground">失败步骤</p>
          <div className="mt-2 space-y-2">
            {failed.map((step) => (
              <div key={step.step_id || step.step_type} className="rounded border p-2">
                <p>{step.title || step.step_type}</p>
                {step.result_summary ? (
                  <p className="mt-1 text-muted-foreground text-xs">{step.result_summary}</p>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
