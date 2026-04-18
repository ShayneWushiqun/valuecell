import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { StockAnalysisThreadMemory } from "@/types/stock-analysis-thread-memory";

const formatTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN");
};

type StockAnalysisMemoryCardProps = {
  memory: StockAnalysisThreadMemory;
  showActivate?: boolean;
  onActivate?: (memoryId: number) => void;
  activating?: boolean;
};

export function StockAnalysisMemoryCard({
  memory,
  showActivate = false,
  onActivate,
  activating = false,
}: StockAnalysisMemoryCardProps) {
  return (
    <div className="rounded-xl border p-4">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-medium text-sm">{memory.title}</p>
        <Badge variant={memory.is_active ? "secondary" : "outline"}>
          v{memory.version || "--"}
        </Badge>
        <Badge variant="outline">{memory.stance}</Badge>
        <Badge variant="outline">
          置信度 {Math.round((memory.confidence || 0) * 100)}%
        </Badge>
        <Badge variant="outline">{memory.time_horizon}</Badge>
      </div>
      <p className="mt-2 text-sm">{memory.summary}</p>
      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        <Badge variant="outline">上下文 {memory.linked_context_count}</Badge>
        <Badge variant="outline">消息 {memory.linked_message_count}</Badge>
        <Badge variant="outline">compare {memory.compare_target_count}</Badge>
        <Badge variant="outline">更新于 {formatTime(memory.updated_at)}</Badge>
      </div>
      {memory.support_points_json.length ? (
        <p className="mt-3 text-muted-foreground text-xs">
          支持依据：{memory.support_points_json.slice(0, 2).join("；")}
        </p>
      ) : null}
      {memory.risk_points_json.length ? (
        <p className="mt-1 text-muted-foreground text-xs">
          风险点：{memory.risk_points_json.slice(0, 2).join("；")}
        </p>
      ) : null}
      {showActivate && !memory.is_active && onActivate ? (
        <div className="mt-3 flex justify-end">
          <Button
            size="sm"
            variant="outline"
            onClick={() => onActivate(memory.memory_id)}
            disabled={activating}
          >
            {activating ? "切换中..." : "设为当前"}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
