import { GitBranchPlus, Plus, RefreshCw, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import type { AnalysisContextCard } from "@/types/analysis-context-card";

type StockAnalysisContextCardProps = {
  item: AnalysisContextCard;
  isSelectedForFork: boolean;
  isInCompare: boolean;
  recentRefreshState?: {
    status: "refreshed" | "skipped" | "failed";
    reason?: string | null;
  } | null;
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

const resolveRefreshStatus = (
  item: AnalysisContextCard,
  recentRefreshState?: StockAnalysisContextCardProps["recentRefreshState"],
) => {
  if (recentRefreshState?.status === "refreshed") {
    return {
      label: "刚刚更新",
      description: recentRefreshState.reason || "内容已刷新，可继续参考",
      variant: "outline" as const,
    };
  }
  if (recentRefreshState?.status === "failed") {
    return {
      label: "刷新失败",
      description: recentRefreshState.reason || "稍后可重试刷新",
      variant: "destructive" as const,
    };
  }
  if (recentRefreshState?.status === "skipped") {
    return {
      label: "本轮未刷新",
      description: recentRefreshState.reason || "这张卡片本轮没有更新",
      variant: "outline" as const,
    };
  }
  if (!item.refresh_supported) {
    return {
      label: "暂不支持刷新",
      description: "当前只能继续参考已有结果",
      variant: "outline" as const,
    };
  }
  if (item.is_stale) {
    return {
      label: "内容偏旧",
      description: "建议刷新后再继续使用",
      variant: "destructive" as const,
    };
  }
  return {
    label: "可直接参考",
    description: "当前时效可接受",
    variant: "secondary" as const,
  };
};

export function StockAnalysisContextCard({
  item,
  isSelectedForFork,
  isInCompare,
  recentRefreshState,
  onToggleSelect,
  onTogglePin,
  onDelete,
  onRefresh,
  onAddToCompare,
  onRemoveFromCompare,
  onForkSingle,
}: StockAnalysisContextCardProps) {
  const refreshStatus = resolveRefreshStatus(item, recentRefreshState);

  return (
    <div className="rounded-xl border p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{item.source_module}</Badge>
            {item.is_pinned ? <Badge variant="secondary">置顶</Badge> : null}
            {item.freshness_label ? (
              <Badge variant={item.is_stale ? "destructive" : "outline"}>
                {item.freshness_label}
              </Badge>
            ) : null}
            <Badge variant={refreshStatus.variant}>{refreshStatus.label}</Badge>
          </div>
          <div>
            <p className="font-medium text-sm">{item.title}</p>
            {item.subtitle ? (
              <p className="mt-1 text-muted-foreground text-xs">{item.subtitle}</p>
            ) : null}
            <p className="mt-1 text-muted-foreground text-xs">{refreshStatus.description}</p>
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
      <p className="mt-3 line-clamp-2 text-sm">{item.summary}</p>
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
          <Badge variant="outline">更新于 {formatTime(item.generated_at)}</Badge>
        ) : null}
        {item.data_time ? (
          <Badge variant="outline">数据时间 {formatTime(item.data_time)}</Badge>
        ) : null}
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
          立即刷新
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() =>
            isInCompare ? onRemoveFromCompare(item) : onAddToCompare(item)
          }
        >
          <Plus className="size-4" />
          {isInCompare ? "移出对比" : "加入当前对比"}
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
