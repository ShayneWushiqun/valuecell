import { GitBranchPlus, Plus, RefreshCw, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import type { AnalysisContextCard } from "@/types/analysis-context-card";

type StockAnalysisContextCardProps = {
  item: AnalysisContextCard;
  isSelectedForFork: boolean;
  isInCompare: boolean;
  onToggleSelect: (contextId: number) => void;
  onTogglePin: (contextId: number, isPinned: boolean) => void;
  onDelete: (contextId: number) => void;
  onRefresh: (contextId: number) => void;
  onAddToCompare: (card: AnalysisContextCard) => void;
  onRemoveFromCompare: (card: AnalysisContextCard) => void;
  onForkSingle: (card: AnalysisContextCard) => void;
};

const formatTime = (value?: string | null) => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN");
};

export function StockAnalysisContextCard({
  item,
  isSelectedForFork,
  isInCompare,
  onToggleSelect,
  onTogglePin,
  onDelete,
  onRefresh,
  onAddToCompare,
  onRemoveFromCompare,
  onForkSingle,
}: StockAnalysisContextCardProps) {
  return (
    <div className="rounded-xl border p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{item.context_type}</Badge>
            <Badge variant="outline">{item.source_module}</Badge>
            {item.freshness_label ? (
              <Badge variant={item.is_stale ? "destructive" : "outline"}>
                {item.freshness_label}
              </Badge>
            ) : null}
            {item.refresh_recommended ? (
              <Badge variant="outline">建议刷新</Badge>
            ) : null}
            {item.is_pinned ? <Badge variant="outline">Pinned</Badge> : null}
          </div>
          <div>
            <p className="font-medium text-sm">{item.title}</p>
            {item.subtitle ? (
              <p className="mt-1 text-muted-foreground text-xs">{item.subtitle}</p>
            ) : null}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Checkbox
            checked={isSelectedForFork}
            onCheckedChange={() => onToggleSelect(item.context_id)}
            aria-label="select context for fork"
          />
        </div>
      </div>
      <p className="mt-3 text-sm">{item.summary}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {item.ticker_refs_json.map((ref) => (
          <Badge key={ref} variant="outline">
            {ref}
          </Badge>
        ))}
        {item.theme_refs_json.map((ref) => (
          <Badge key={ref} variant="outline">
            {ref}
          </Badge>
        ))}
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {item.generated_at ? (
          <Badge variant="outline">生成时间：{formatTime(item.generated_at)}</Badge>
        ) : null}
        {item.data_time ? (
          <Badge variant="outline">数据时间：{formatTime(item.data_time)}</Badge>
        ) : null}
        <Badge variant="outline">
          {item.refresh_supported ? "支持刷新" : "不支持直接刷新"}
        </Badge>
      </div>
      {item.staleness_hint ? (
        <p className="mt-3 text-muted-foreground text-xs">{item.staleness_hint}</p>
      ) : null}
      <div className="mt-4 flex flex-wrap gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => onTogglePin(item.context_id, item.is_pinned)}
        >
          {item.is_pinned ? "取消置顶" : "置顶"}
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={!item.refresh_supported}
          onClick={() => onRefresh(item.context_id)}
        >
          <RefreshCw className="size-4" />
          刷新
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() =>
            isInCompare ? onRemoveFromCompare(item) : onAddToCompare(item)
          }
        >
          <Plus className="size-4" />
          {isInCompare ? "移出对比" : "加入对比"}
        </Button>
        <Button size="sm" variant="outline" onClick={() => onForkSingle(item)}>
          <GitBranchPlus className="size-4" />
          用此分叉
        </Button>
        <Button size="sm" variant="outline" onClick={() => onDelete(item.context_id)}>
          <Trash2 className="size-4" />
          删除
        </Button>
      </div>
    </div>
  );
}
