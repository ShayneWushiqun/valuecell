import { StockAnalysisMemoryCard } from "@/app/home/components/stock-analysis-memory-card";
import type { StockAnalysisThreadMemory } from "@/types/stock-analysis-thread-memory";

type StockAnalysisMemoryHistoryProps = {
  memories: StockAnalysisThreadMemory[];
  onActivate: (memoryId: number) => void;
  activating?: boolean;
};

export function StockAnalysisMemoryHistory({
  memories,
  onActivate,
  activating = false,
}: StockAnalysisMemoryHistoryProps) {
  if (!memories.length) {
    return (
      <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
        当前线程还没有研究记忆历史。
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {memories.map((memory) => (
        <StockAnalysisMemoryCard
          key={memory.memory_id}
          memory={memory}
          showActivate
          onActivate={onActivate}
          activating={activating}
        />
      ))}
    </div>
  );
}
