import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type {
  DecisionContextEventSummary,
  DecisionContextWindow,
} from "@/types/decision-context-window";

const renderEventList = (title: string, items: DecisionContextEventSummary[]) => (
  <div className="rounded-xl border bg-card p-4">
    <div className="flex items-center justify-between">
      <p className="font-medium text-sm">{title}</p>
      <Badge variant="outline">{items.length}</Badge>
    </div>
    <div className="mt-3 space-y-2">
      {items.length ? (
        items.map((item) => (
          <div key={`${title}-${item.event_id || item.summary}`} className="rounded-lg border bg-background p-3">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <Badge variant="outline">{item.layer}</Badge>
              <Badge variant="outline">{item.source}</Badge>
              {item.importance_score !== null ? (
                <Badge variant="outline">强度 {item.importance_score}</Badge>
              ) : null}
            </div>
            <p className="mt-2 text-sm">{item.summary}</p>
            {item.tradeability_hint ? (
              <p className="mt-1 text-muted-foreground text-sm">{item.tradeability_hint}</p>
            ) : null}
          </div>
        ))
      ) : (
        <p className="text-muted-foreground text-sm">暂无该类证据。</p>
      )}
    </div>
  </div>
);

export default function DecisionContextWindowDetail({
  item,
  open,
  onOpenChange,
}: {
  item: DecisionContextWindow | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>{item?.display_name || "决策上下文"}</DialogTitle>
          <DialogDescription>
            这里展示最近时间窗内的支持、反对与风险链条，不构成交易指令。
          </DialogDescription>
        </DialogHeader>
        {!item ? null : (
          <div className="space-y-4">
            <div className="rounded-xl border bg-card p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">{item.ticker}</Badge>
                <Badge variant="secondary">{item.window_size} 日窗口</Badge>
                <Badge variant="outline">风险 {item.risk_level}</Badge>
                <Badge variant="outline">分歧 {item.disagreement_level}</Badge>
              </div>
              <p className="mt-3 text-sm">{item.summary}</p>
              <div className="mt-3 flex flex-wrap gap-2 text-muted-foreground text-xs">
                {item.position_state ? <span>持仓 {item.position_state}</span> : null}
                {item.expectation_state ? <span>预期 {item.expectation_state}</span> : null}
                {item.tradeability_state ? <span>{item.tradeability_state}</span> : null}
                {item.role_label ? <span>角色 {item.role_label}</span> : null}
                {item.trend_quality ? <span>趋势 {item.trend_quality}</span> : null}
              </div>
            </div>

            <div className="grid gap-4 xl:grid-cols-3">
              {renderEventList("支持证据", item.support_events_json)}
              {renderEventList("反对证据", item.opposing_events_json)}
              {renderEventList("风险证据", item.risk_events_json)}
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <div className="rounded-xl border bg-card p-4">
                <p className="font-medium text-sm">当前规则裁决摘要</p>
                <div className="mt-3 flex flex-wrap gap-2 text-xs">
                  <Badge variant="outline">{String(item.judgement_snapshot_json.action || "继续观察")}</Badge>
                  <Badge variant="outline">
                    置信度 {Number(item.judgement_snapshot_json.confidence || 0)}
                  </Badge>
                </div>
                <p className="mt-3 text-sm">
                  {String(item.judgement_snapshot_json.summary || "当前以规则版摘要为主。")}
                </p>
                {Array.isArray(item.judgement_snapshot_json.invalid_conditions) &&
                item.judgement_snapshot_json.invalid_conditions[0] ? (
                  <p className="mt-2 text-muted-foreground text-sm">
                    失效条件：{String(item.judgement_snapshot_json.invalid_conditions[0])}
                  </p>
                ) : null}
              </div>
              <div className="rounded-xl border bg-card p-4">
                <p className="font-medium text-sm">退出流动性计划</p>
                <p className="mt-3 text-sm">{item.exit_liquidity_plan || "当前暂无额外退出流动性提示。"}</p>
                {Array.isArray(item.judgement_snapshot_json.risk_controls) &&
                item.judgement_snapshot_json.risk_controls[0] ? (
                  <p className="mt-2 text-muted-foreground text-sm">
                    风控提示：{String(item.judgement_snapshot_json.risk_controls[0])}
                  </p>
                ) : null}
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
