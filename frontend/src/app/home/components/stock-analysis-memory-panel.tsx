import { useState } from "react";
import { History, RefreshCw } from "lucide-react";
import { StockAnalysisMemoryCard } from "@/app/home/components/stock-analysis-memory-card";
import { StockAnalysisMemoryHistory } from "@/app/home/components/stock-analysis-memory-history";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import type { StockAnalysisThreadMemory } from "@/types/stock-analysis-thread-memory";

type StockAnalysisMemoryPanelProps = {
  activeMemory: StockAnalysisThreadMemory | null;
  memories: StockAnalysisThreadMemory[];
  isLoading?: boolean;
  onCapture: () => void;
  onRefresh: (memoryId: number) => void;
  onActivate: (memoryId: number) => void;
  capturePending?: boolean;
  refreshPending?: boolean;
  activatePending?: boolean;
};

export function StockAnalysisMemoryPanel({
  activeMemory,
  memories,
  isLoading = false,
  onCapture,
  onRefresh,
  onActivate,
  capturePending = false,
  refreshPending = false,
  activatePending = false,
}: StockAnalysisMemoryPanelProps) {
  const [showHistory, setShowHistory] = useState(false);

  return (
    <div className="rounded-xl border p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-medium text-sm">研究记忆</p>
          <p className="text-muted-foreground text-xs">
            显式沉淀当前线程的研究结论，并作为后续问答的辅助输入。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={onCapture} disabled={capturePending}>
            {capturePending ? "生成中..." : "生成研究记忆"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => activeMemory && onRefresh(activeMemory.memory_id)}
            disabled={!activeMemory || refreshPending}
          >
            <RefreshCw className="size-4" />
            {refreshPending ? "刷新中..." : "刷新当前研究记忆"}
          </Button>
          <Button size="sm" variant="outline" onClick={() => setShowHistory((v) => !v)}>
            <History className="size-4" />
            {showHistory ? "收起历史" : "查看记忆历史"}
          </Button>
        </div>
      </div>
      <div className="mt-4 space-y-3">
        {isLoading ? (
          <div className="flex min-h-24 items-center justify-center rounded-xl border border-dashed">
            <Spinner className="size-5" />
          </div>
        ) : activeMemory ? (
          <StockAnalysisMemoryCard memory={activeMemory} />
        ) : (
          <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
            当前线程还没有 active memory。可以先基于已有上下文、compare targets 和最近关键问答生成第一份研究记忆。
          </div>
        )}
        {showHistory ? (
          <StockAnalysisMemoryHistory
            memories={memories}
            onActivate={onActivate}
            activating={activatePending}
          />
        ) : null}
      </div>
    </div>
  );
}
