import { GitBranchPlus, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { StockAnalysisCompareTarget } from "@/types/stock-analysis-thread";

type StockAnalysisCompareTrayProps = {
  compareTargets: StockAnalysisCompareTarget[];
  onRemove: (target: StockAnalysisCompareTarget) => void;
  onFork: () => void;
  isMutating?: boolean;
};

export function StockAnalysisCompareTray({
  compareTargets,
  onRemove,
  onFork,
  isMutating = false,
}: StockAnalysisCompareTrayProps) {
  if (!compareTargets.length) {
    return (
      <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
        当前还没有显式对比对象。可从线程 refs 或右侧上下文卡片加入对比。
      </div>
    );
  }

  return (
    <div className="rounded-xl border p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-medium text-sm">当前对比对象</p>
          <p className="text-muted-foreground text-xs">
            显式管理本线程正在比较的对象、来源和主次顺序。
          </p>
        </div>
        <Button size="sm" variant="outline" onClick={onFork}>
          <GitBranchPlus className="size-4" />
          生成对比线程
        </Button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {compareTargets.map((target) => (
          <div
            key={`${target.target_type}:${target.ref}:${target.source_module}`}
            className="flex items-center gap-2 rounded-lg border px-3 py-2"
          >
            <Badge variant={target.role === "primary" ? "secondary" : "outline"}>
              {target.label}
            </Badge>
            <Badge variant="outline">{target.source_module}</Badge>
            <Badge variant="outline">{target.role}</Badge>
            <Button
              size="icon"
              variant="ghost"
              className="size-7"
              disabled={isMutating}
              onClick={() => onRemove(target)}
            >
              <X className="size-4" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
