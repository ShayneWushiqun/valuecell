import { Badge } from "@/components/ui/badge";

type StockAnalysisThreadSummaryProps = {
  compareTargetCount: number;
  staleCount: number;
  refreshRecommendedCount: number;
  savedEvidenceCount: number;
  activeMemoryAvailable: boolean;
  activeCompressionAvailable: boolean;
  compressionRecommended: boolean;
  activeCompressionStale: boolean;
  uncompressedMessageCount: number;
  compressionReason?: string | null;
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
  activeMemoryAvailable,
  activeCompressionAvailable,
  compressionRecommended,
  activeCompressionStale,
  uncompressedMessageCount,
  compressionReason,
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
        <Badge variant="outline">
          研究记忆 {activeMemoryAvailable ? "已启用" : "未启用"}
        </Badge>
        <Badge variant="outline">
          对话压缩 {activeCompressionAvailable ? "已启用" : "未启用"}
        </Badge>
        <Badge variant="outline">
          未压缩消息 {uncompressedMessageCount}
        </Badge>
        <Badge variant={compressionRecommended ? "secondary" : "outline"}>
          {compressionRecommended ? "建议压缩" : "当前无需压缩"}
        </Badge>
        <Badge variant={activeCompressionStale ? "secondary" : "outline"}>
          {activeCompressionStale ? "压缩偏旧" : "压缩可用"}
        </Badge>
      </div>
      <div className="mt-3 space-y-2 text-sm">
        <p className="text-muted-foreground">
          最近一次批量刷新：{formatTime(lastRefreshAt)}
        </p>
        <p>{lastRefreshSummary || "当前还没有批量刷新记录。"}</p>
        <p className="text-muted-foreground">
          {compressionReason || "当前线程如果继续增长，可手动整理对话。"}
        </p>
      </div>
    </div>
  );
}
