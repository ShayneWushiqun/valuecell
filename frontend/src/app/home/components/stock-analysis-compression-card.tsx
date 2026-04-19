import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { StockAnalysisThreadCompression } from "@/types/stock-analysis-thread-compression";

const formatTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN");
};

type StockAnalysisCompressionCardProps = {
  compression: StockAnalysisThreadCompression;
  showActivate?: boolean;
  onActivate?: (compressionId: number) => void;
  activating?: boolean;
};

export function StockAnalysisCompressionCard({
  compression,
  showActivate = false,
  onActivate,
  activating = false,
}: StockAnalysisCompressionCardProps) {
  return (
    <div className="rounded-xl border p-4">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-medium text-sm">{compression.title}</p>
        <Badge variant={compression.is_active ? "secondary" : "outline"}>
          v{compression.version || "--"}
        </Badge>
        <Badge variant="outline">覆盖 {compression.covered_message_count} 条消息</Badge>
        <Badge variant="outline">更新于 {formatTime(compression.updated_at)}</Badge>
      </div>
      <p className="mt-2 text-sm">{compression.summary}</p>
      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        <Badge variant="outline">
          截止 {compression.covered_until_message_id || "--"}
        </Badge>
        <Badge variant="outline">关键消息 {compression.source_message_count}</Badge>
        <Badge variant="outline">{compression.current_focus || "当前焦点"}</Badge>
      </div>
      {compression.open_questions_json.length ? (
        <p className="mt-3 text-muted-foreground text-xs">
          未完问题：{compression.open_questions_json.slice(0, 2).join("；")}
        </p>
      ) : null}
      {compression.recent_refresh_notes_json.length ? (
        <p className="mt-1 text-muted-foreground text-xs">
          最近刷新：{compression.recent_refresh_notes_json.slice(0, 1).join("；")}
        </p>
      ) : null}
      {showActivate && !compression.is_active && onActivate ? (
        <div className="mt-3 flex justify-end">
          <Button
            size="sm"
            variant="outline"
            onClick={() => onActivate(compression.compression_id)}
            disabled={activating}
          >
            {activating ? "切换中..." : "设为当前"}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
