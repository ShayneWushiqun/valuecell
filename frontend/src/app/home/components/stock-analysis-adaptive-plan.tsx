import { Badge } from "@/components/ui/badge";

type StockAnalysisAdaptivePlanProps = {
  planningProfile?: string | null;
  planningReasoning?: string | null;
  preferredEvidenceOrder: string[];
  planningAdjustments: string[];
  processConfidenceHint?: string | null;
  providerStopReason?: string | null;
  providerSkippedReason?: string | null;
  evidencePlanSummary?: string | null;
};

export function StockAnalysisAdaptivePlan({
  planningProfile,
  planningReasoning,
  preferredEvidenceOrder,
  planningAdjustments,
  processConfidenceHint,
  providerStopReason,
  providerSkippedReason,
  evidencePlanSummary,
}: StockAnalysisAdaptivePlanProps) {
  if (
    !planningProfile &&
    !planningReasoning &&
    !preferredEvidenceOrder.length &&
    !planningAdjustments.length &&
    !providerStopReason &&
    !providerSkippedReason &&
    !evidencePlanSummary
  ) {
    return null;
  }

  return (
    <div className="rounded-lg border border-dashed p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-medium">Adaptive Planning</p>
        {planningProfile ? <Badge variant="secondary">{planningProfile}</Badge> : null}
      </div>
      {evidencePlanSummary ? (
        <p className="mt-2 text-muted-foreground">{evidencePlanSummary}</p>
      ) : null}
      {planningReasoning ? (
        <p className="mt-2 text-muted-foreground">{planningReasoning}</p>
      ) : null}
      {preferredEvidenceOrder.length ? (
        <p className="mt-2">
          <span className="font-medium">evidence order:</span>{" "}
          {preferredEvidenceOrder.join(" -> ")}
        </p>
      ) : null}
      {planningAdjustments.length ? (
        <p className="mt-2">
          <span className="font-medium">planning adjustments:</span>{" "}
          {planningAdjustments.join("；")}
        </p>
      ) : null}
      {providerStopReason ? (
        <p className="mt-2">
          <span className="font-medium">provider stop:</span> {providerStopReason}
        </p>
      ) : null}
      {providerSkippedReason ? (
        <p className="mt-2">
          <span className="font-medium">provider skipped:</span> {providerSkippedReason}
        </p>
      ) : null}
      {processConfidenceHint ? (
        <p className="mt-2 text-muted-foreground text-xs">{processConfidenceHint}</p>
      ) : null}
    </div>
  );
}
