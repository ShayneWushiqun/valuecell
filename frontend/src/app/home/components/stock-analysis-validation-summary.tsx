import { Badge } from "@/components/ui/badge";

type StockAnalysisValidationSummaryProps = {
  validationSummary?: Record<string, unknown> | null;
  thesisChangeHint?: string | null;
};

const toStringArray = (value: unknown) =>
  Array.isArray(value)
    ? value.map((item) => String(item)).filter(Boolean)
    : [];

export function StockAnalysisValidationSummary({
  validationSummary,
  thesisChangeHint,
}: StockAnalysisValidationSummaryProps) {
  if (!validationSummary || !Object.keys(validationSummary).length) {
    return null;
  }
  const thesisStatus = String(validationSummary.thesis_status || "");
  const summary = String(validationSummary.summary || "");
  const supportPoints = toStringArray(validationSummary.support_points);
  const opposingPoints = toStringArray(validationSummary.opposing_points);
  const riskPoints = toStringArray(validationSummary.risk_points);
  const evidenceConflictLevel = String(validationSummary.evidence_conflict_level || "");
  const resolutionSuggestion = String(validationSummary.resolution_suggestion || "");
  const thesisConfidenceHint = String(validationSummary.thesis_confidence_hint || "");

  return (
    <div className="rounded-lg border border-dashed p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-medium">Thesis Validation</p>
        {thesisStatus ? <Badge variant="secondary">{thesisStatus}</Badge> : null}
        {evidenceConflictLevel ? (
          <Badge variant="outline">conflict {evidenceConflictLevel}</Badge>
        ) : null}
      </div>
      {summary ? <p className="mt-2 text-muted-foreground">{summary}</p> : null}
      {thesisChangeHint ? (
        <p className="mt-2 text-muted-foreground text-xs">{thesisChangeHint}</p>
      ) : null}
      {resolutionSuggestion ? (
        <p className="mt-2 text-xs">resolution: {resolutionSuggestion}</p>
      ) : null}
      {thesisConfidenceHint ? (
        <p className="mt-2 text-muted-foreground text-xs">{thesisConfidenceHint}</p>
      ) : null}
      {supportPoints.length ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {supportPoints.map((item) => (
            <Badge key={`support-${item}`} variant="outline" className="whitespace-normal">
              support: {item}
            </Badge>
          ))}
        </div>
      ) : null}
      {opposingPoints.length ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {opposingPoints.map((item) => (
            <Badge key={`oppose-${item}`} variant="outline" className="whitespace-normal">
              opposing: {item}
            </Badge>
          ))}
        </div>
      ) : null}
      {riskPoints.length ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {riskPoints.map((item) => (
            <Badge key={`risk-${item}`} variant="outline" className="whitespace-normal">
              risk: {item}
            </Badge>
          ))}
        </div>
      ) : null}
    </div>
  );
}
