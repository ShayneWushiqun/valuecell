import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { DecisionContextWindow } from "@/types/decision-context-window";
import { Link } from "react-router";

const getRiskClassName = (riskLevel: string) => {
  if (riskLevel === "高") return "bg-red-500/10 text-red-500";
  if (riskLevel === "中") return "bg-orange-500/10 text-orange-500";
  return "bg-emerald-500/10 text-emerald-500";
};

export default function DecisionContextWindowCard({
  item,
  onSelect,
  reviewMeta,
}: {
  item: DecisionContextWindow;
  onSelect: (item: DecisionContextWindow) => void;
  reviewMeta?: {
    reviewId: number;
    outcomeStatus: string;
  } | null;
}) {
  const action = String(item.judgement_snapshot_json.action || "继续观察");
  const confidence = Number(item.judgement_snapshot_json.confidence || 0);

  return (
    <div className="rounded-2xl border bg-background p-4">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-semibold text-base">{item.display_name}</p>
        <Badge variant="outline">{item.ticker}</Badge>
        <Badge variant="secondary">{item.window_size} 日</Badge>
        <Badge className={getRiskClassName(item.risk_level)}>
          风险 {item.risk_level}
        </Badge>
        <Badge variant="outline">分歧 {item.disagreement_level}</Badge>
      </div>
      <p className="mt-3 text-sm">{item.summary}</p>
      <div className="mt-3 flex flex-wrap gap-2 text-muted-foreground text-xs">
        {item.topic_name ? <span>题材 {item.topic_name}</span> : null}
        {item.market_state ? <span>市场 {item.market_state}</span> : null}
        {item.position_state ? <span>持仓 {item.position_state}</span> : null}
        {item.tradeability_state ? <span>{item.tradeability_state}</span> : null}
        {item.role_label ? <span>角色 {item.role_label}</span> : null}
        {item.trend_quality ? <span>趋势 {item.trend_quality}</span> : null}
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-muted-foreground text-xs">
        <span>支持 {item.support_count}</span>
        <span>反对 {item.opposing_count}</span>
        <span>风险 {item.risk_count}</span>
        <span>裁决 {action}</span>
        <span>置信度 {confidence}</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button size="sm" variant="outline" onClick={() => onSelect(item)}>
          查看详情
        </Button>
        <Button asChild size="sm" variant="outline">
          <Link
            to={`/home/stock-analysis?sourceModule=decision_context_window&sourceRef=${item.window_id}&createThread=1`}
          >
            加入研究线程
          </Link>
        </Button>
        {reviewMeta ? (
          <Button asChild size="sm" variant="outline">
            <Link to="/home/decision-reviews">
              查看回看结果 · {reviewMeta.outcomeStatus}
            </Link>
          </Button>
        ) : (
          <div className="flex items-center text-muted-foreground text-xs">
            暂无关联回看结果
          </div>
        )}
      </div>
    </div>
  );
}
