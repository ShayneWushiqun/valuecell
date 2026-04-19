import { Badge } from "@/components/ui/badge";

type StockAnalysisEvidenceConflictProps = {
  evidenceConflictSummary?: Record<string, unknown> | null;
  thesisConfidenceHint?: string | null;
};

const toStringArray = (value: unknown) =>
  Array.isArray(value) ? value.map((item) => String(item)).filter(Boolean) : [];

export function StockAnalysisEvidenceConflict({
  evidenceConflictSummary,
  thesisConfidenceHint,
}: StockAnalysisEvidenceConflictProps) {
  if (!evidenceConflictSummary || !Object.keys(evidenceConflictSummary).length) {
    return null;
  }
  const conflictLevel = String(evidenceConflictSummary.conflict_level || "");
  const supporting = toStringArray(evidenceConflictSummary.supporting_evidence);
  const opposing = toStringArray(evidenceConflictSummary.opposing_evidence);
  const risk = toStringArray(evidenceConflictSummary.risk_evidence);
  const neutral = toStringArray(evidenceConflictSummary.neutral_evidence);
  const conflictReason = String(evidenceConflictSummary.conflict_reason || "");
  const resolutionSuggestion = String(
    evidenceConflictSummary.resolution_suggestion || "",
  );

  return (
    <div className="rounded-lg border border-dashed p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-medium">Evidence Conflict</p>
        {conflictLevel ? <Badge variant="secondary">{conflictLevel}</Badge> : null}
      </div>
      {conflictReason ? (
        <p className="mt-2 text-muted-foreground">{conflictReason}</p>
      ) : null}
      {supporting.length ? (
        <p className="mt-2">
          <span className="font-medium">supporting:</span> {supporting.join("；")}
        </p>
      ) : null}
      {opposing.length ? (
        <p className="mt-2">
          <span className="font-medium">opposing:</span> {opposing.join("；")}
        </p>
      ) : null}
      {risk.length ? (
        <p className="mt-2">
          <span className="font-medium">risk:</span> {risk.join("；")}
        </p>
      ) : null}
      {neutral.length ? (
        <p className="mt-2">
          <span className="font-medium">neutral:</span> {neutral.join("；")}
        </p>
      ) : null}
      {resolutionSuggestion ? (
        <p className="mt-2">
          <span className="font-medium">resolution:</span> {resolutionSuggestion}
        </p>
      ) : null}
      {thesisConfidenceHint ? (
        <p className="mt-2 text-muted-foreground text-xs">{thesisConfidenceHint}</p>
      ) : null}
    </div>
  );
}
