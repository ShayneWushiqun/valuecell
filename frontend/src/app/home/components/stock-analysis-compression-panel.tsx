import { useState } from "react";
import { History, Scissors, RefreshCw } from "lucide-react";
import { StockAnalysisCompressionCard } from "@/app/home/components/stock-analysis-compression-card";
import { StockAnalysisCompressionHistory } from "@/app/home/components/stock-analysis-compression-history";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import type { StockAnalysisThreadCompression } from "@/types/stock-analysis-thread-compression";

type StockAnalysisCompressionPanelProps = {
  activeCompression: StockAnalysisThreadCompression | null;
  compressions: StockAnalysisThreadCompression[];
  compressionRecommended: boolean;
  compressionReason?: string | null;
  uncompressedMessageCount: number;
  estimatedHistorySize: number;
  activeCompressionStale: boolean;
  isLoading?: boolean;
  onCapture: () => void;
  onRefresh: (compressionId: number) => void;
  onActivate: (compressionId: number) => void;
  capturePending?: boolean;
  refreshPending?: boolean;
  activatePending?: boolean;
};

export function StockAnalysisCompressionPanel({
  activeCompression,
  compressions,
  compressionRecommended,
  compressionReason,
  uncompressedMessageCount,
  estimatedHistorySize,
  activeCompressionStale,
  isLoading = false,
  onCapture,
  onRefresh,
  onActivate,
  capturePending = false,
  refreshPending = false,
  activatePending = false,
}: StockAnalysisCompressionPanelProps) {
  const [showHistory, setShowHistory] = useState(false);

  return (
    <div className="rounded-xl border p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-medium text-sm">Conversation Compression</p>
          <p className="text-muted-foreground text-xs">
            显式整理较长聊天历史，保留 active compression 和最近原始消息的分层输入。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={onCapture} disabled={capturePending}>
            <Scissors className="size-4" />
            {capturePending ? "整理中..." : "整理当前对话"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() =>
              activeCompression && onRefresh(activeCompression.compression_id)
            }
            disabled={!activeCompression || refreshPending}
          >
            <RefreshCw className="size-4" />
            {refreshPending ? "刷新中..." : "刷新当前压缩摘要"}
          </Button>
          <Button size="sm" variant="outline" onClick={() => setShowHistory((v) => !v)}>
            <History className="size-4" />
            {showHistory ? "收起历史" : "查看压缩历史"}
          </Button>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        <span className="rounded-md border px-2 py-1">
          未压缩消息 {uncompressedMessageCount}
        </span>
        <span className="rounded-md border px-2 py-1">
          历史大小约 {estimatedHistorySize}
        </span>
        <span className="rounded-md border px-2 py-1">
          {compressionRecommended ? "建议重新压缩" : "当前无需压缩"}
        </span>
        <span className="rounded-md border px-2 py-1">
          {activeCompressionStale ? "当前 active compression 偏旧" : "当前 active compression 可用"}
        </span>
      </div>
      <p className="mt-2 text-muted-foreground text-xs">
        {compressionReason || "当前线程消息较短时，可暂时不整理。"}
      </p>
      <div className="mt-4 space-y-3">
        {isLoading ? (
          <div className="flex min-h-24 items-center justify-center rounded-xl border border-dashed">
            <Spinner className="size-5" />
          </div>
        ) : activeCompression ? (
          <StockAnalysisCompressionCard compression={activeCompression} />
        ) : (
          <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
            当前线程还没有 active compression。消息较长、最近 compare/refresh/tooling 变化较多时，可以显式整理当前对话。
          </div>
        )}
        {showHistory ? (
          <StockAnalysisCompressionHistory
            compressions={compressions}
            onActivate={onActivate}
            activating={activatePending}
          />
        ) : null}
      </div>
    </div>
  );
}
