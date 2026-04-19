import { StockAnalysisCompressionCard } from "@/app/home/components/stock-analysis-compression-card";
import type { StockAnalysisThreadCompression } from "@/types/stock-analysis-thread-compression";

type StockAnalysisCompressionHistoryProps = {
  compressions: StockAnalysisThreadCompression[];
  onActivate: (compressionId: number) => void;
  activating?: boolean;
};

export function StockAnalysisCompressionHistory({
  compressions,
  onActivate,
  activating = false,
}: StockAnalysisCompressionHistoryProps) {
  if (!compressions.length) {
    return (
      <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
        当前线程还没有对话压缩历史。
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {compressions.map((compression) => (
        <StockAnalysisCompressionCard
          key={compression.compression_id}
          compression={compression}
          showActivate
          onActivate={onActivate}
          activating={activating}
        />
      ))}
    </div>
  );
}
