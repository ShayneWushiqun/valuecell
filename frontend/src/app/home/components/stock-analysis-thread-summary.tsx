import { Badge } from "@/components/ui/badge";

type StockAnalysisThreadSummaryProps = {
  compareTargetCount: number;
  staleCount: number;
  refreshRecommendedCount: number;
  savedEvidenceCount: number;
  lastRefreshAt?: string | null;
  lastRefreshSummary?: string | null;
};

const formatTime = (value?: string | null) => {
  if (!value) return "暂无";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN");
};

export function StockAnalysisThreadSummary({
  compareTargetCount,
  staleCount,
  refreshRecommendedCount,
  savedEvidenceCount,
  lastRefreshAt,
  lastRefreshSummary,
}: StockAnalysisThreadSummaryProps) {
  return (
    <div className="rounded-xl border p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary">研究流摘要</Badge>
        <Badge variant="outline">对比对象 {compareTargetCount}</Badge>
        <Badge variant="outline">较旧上下文 {staleCount}</Badge>
        <Badge variant="outline">建议刷新 {refreshRecommendedCount}</Badge>
        <Badge variant="outline">长期证据 {savedEvidenceCount}</Badge>
      </div>
      <div className="mt-3 space-y-2 text-sm">
        <p className="text-muted-foreground">
          最近一次批量刷新：{formatTime(lastRefreshAt)}
        </p>
        <p>{lastRefreshSummary || "当前还没有批量刷新记录。"}</p>
      </div>
    </div>
  );
}
