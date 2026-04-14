import {
  AlertTriangle,
  Pencil,
  Plus,
  RefreshCcw,
  Trash2,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router";
import { toast } from "sonner";
import {
  useGetHoldingExitSignal,
  useGetHoldingExitSignals,
  useRefreshHoldingExitSignal,
} from "@/api/holding-exit-signal";
import {
  useCreateHolding,
  useDeleteHolding,
  useGetPortfolioOverview,
  useRefreshDailyBriefing,
  useRefreshHoldingDiagnosis,
  useUpdateHolding,
} from "@/api/portfolio";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import type { HoldingExitSignal } from "@/types/holding-exit-signal";
import type { CreateHoldingRequest, UserHolding } from "@/types/portfolio";

type HoldingFormState = {
  ticker: string;
  asset_name: string;
  quantity: string;
  cost_price: string;
  position_weight: string;
  buy_date: string;
  thesis_note: string;
  notes: string;
};

type PortfolioOverviewProps = {
  showDailySummary?: boolean;
  sectionTitle?: string;
  sectionDescription?: string;
  className?: string;
};

const emptyForm: HoldingFormState = {
  ticker: "",
  asset_name: "",
  quantity: "",
  cost_price: "",
  position_weight: "",
  buy_date: "",
  thesis_note: "",
  notes: "",
};

const getActionBadgeClassName = (action?: string | null) => {
  if (action === "卖出") return "bg-red-500/10 text-red-500";
  if (action === "减仓") return "bg-orange-500/10 text-orange-500";
  if (action === "持有") return "bg-emerald-500/10 text-emerald-500";
  return "bg-muted text-muted-foreground";
};

const getRiskBadgeClassName = (risk?: string | null) => {
  if (risk === "高") return "bg-red-500/10 text-red-500";
  if (risk === "中") return "bg-orange-500/10 text-orange-500";
  return "bg-emerald-500/10 text-emerald-500";
};

const getExitActionBadgeClassName = (action?: string | null) => {
  if (action === "纪律止损") return "bg-red-500/10 text-red-500";
  if (action === "保护利润") return "bg-amber-500/10 text-amber-600";
  if (action === "减仓观察") return "bg-orange-500/10 text-orange-500";
  if (action === "继续持有") return "bg-emerald-500/10 text-emerald-500";
  return "bg-blue-500/10 text-blue-500";
};

const formatPercent = (value?: number | null) => {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
};

const formatPrice = (value?: number | null) => {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return value.toFixed(2);
};

const buildFormFromHolding = (holding?: UserHolding | null): HoldingFormState => {
  if (!holding) return emptyForm;
  return {
    ticker: holding.ticker,
    asset_name: holding.asset_name || "",
    quantity: String(holding.quantity),
    cost_price: String(holding.cost_price),
    position_weight:
      holding.position_weight === null || holding.position_weight === undefined
        ? ""
        : String(holding.position_weight),
    buy_date: holding.buy_date || "",
    thesis_note: holding.thesis_note || "",
    notes: holding.notes || "",
  };
};

const buildHoldingPayload = (form: HoldingFormState): CreateHoldingRequest | null => {
  const quantity = Number(form.quantity);
  const costPrice = Number(form.cost_price);
  const positionWeight = form.position_weight ? Number(form.position_weight) : null;

  if (!form.ticker.trim()) {
    toast.error("请输入 A 股代码");
    return null;
  }
  if (!Number.isFinite(quantity) || quantity <= 0) {
    toast.error("持仓数量必须大于 0");
    return null;
  }
  if (!Number.isFinite(costPrice) || costPrice <= 0) {
    toast.error("成本价必须大于 0");
    return null;
  }
  if (
    positionWeight !== null &&
    (!Number.isFinite(positionWeight) || positionWeight < 0 || positionWeight > 100)
  ) {
    toast.error("仓位占比必须在 0 到 100 之间");
    return null;
  }

  return {
    ticker: form.ticker.trim(),
    asset_name: form.asset_name.trim() || null,
    quantity,
    cost_price: costPrice,
    position_weight: positionWeight,
    buy_date: form.buy_date || null,
    thesis_note: form.thesis_note.trim() || null,
    notes: form.notes.trim() || null,
  };
};

function HoldingFormDialog({
  open,
  title,
  value,
  pending,
  onOpenChange,
  onChange,
  onSubmit,
}: {
  open: boolean;
  title: string;
  value: HoldingFormState;
  pending: boolean;
  onOpenChange: (open: boolean) => void;
  onChange: (next: HoldingFormState) => void;
  onSubmit: () => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="grid gap-2">
            <Label htmlFor="holding-ticker">股票代码</Label>
            <Input
              id="holding-ticker"
              placeholder="例如 600519 或 SSE:600519"
              value={value.ticker}
              onChange={(event) =>
                onChange({ ...value, ticker: event.target.value })
              }
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="holding-name">股票名称</Label>
            <Input
              id="holding-name"
              placeholder="可选"
              value={value.asset_name}
              onChange={(event) =>
                onChange({ ...value, asset_name: event.target.value })
              }
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="holding-quantity">持仓数量</Label>
            <Input
              id="holding-quantity"
              type="number"
              min="1"
              value={value.quantity}
              onChange={(event) =>
                onChange({ ...value, quantity: event.target.value })
              }
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="holding-cost">成本价</Label>
            <Input
              id="holding-cost"
              type="number"
              min="0"
              step="0.01"
              value={value.cost_price}
              onChange={(event) =>
                onChange({ ...value, cost_price: event.target.value })
              }
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="holding-weight">仓位占比</Label>
            <Input
              id="holding-weight"
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={value.position_weight}
              onChange={(event) =>
                onChange({ ...value, position_weight: event.target.value })
              }
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="holding-buy-date">买入日期</Label>
            <Input
              id="holding-buy-date"
              type="date"
              value={value.buy_date}
              onChange={(event) =>
                onChange({ ...value, buy_date: event.target.value })
              }
            />
          </div>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="holding-thesis">建仓逻辑摘要</Label>
          <Textarea
            id="holding-thesis"
            placeholder="为什么买入，后续主要看什么"
            value={value.thesis_note}
            onChange={(event) =>
              onChange({ ...value, thesis_note: event.target.value })
            }
          />
        </div>

        <div className="grid gap-2">
          <Label htmlFor="holding-notes">备注</Label>
          <Textarea
            id="holding-notes"
            placeholder="补充说明"
            value={value.notes}
            onChange={(event) => onChange({ ...value, notes: event.target.value })}
          />
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button disabled={pending} onClick={onSubmit}>
            {pending ? <Spinner className="size-4" /> : null}
            保存并生成诊断
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function HoldingExitSignalDialog({
  holding,
  open,
  onOpenChange,
}: {
  holding: UserHolding | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const holdingId = holding?.id ?? null;
  const {
    data: exitSignal,
    isLoading,
    isError,
  } = useGetHoldingExitSignal(holdingId, open);
  const refreshExitSignal = useRefreshHoldingExitSignal();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>{holding?.asset_name || holding?.ticker || "持仓裁决"}</DialogTitle>
          <DialogDescription>
            这是持仓处理建议，不等于新开仓建议，也不构成交易指令。
          </DialogDescription>
        </DialogHeader>

        <div className="flex justify-end">
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              if (holdingId) refreshExitSignal.mutate(holdingId);
            }}
            disabled={!holdingId || refreshExitSignal.isPending}
          >
            {refreshExitSignal.isPending ? "刷新中..." : "刷新持仓裁决"}
          </Button>
        </div>

        {isLoading ? (
          <div className="flex min-h-40 items-center justify-center">
            <Spinner className="size-5" />
          </div>
        ) : null}

        {!isLoading && (isError || !exitSignal?.available) ? (
          <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
            {exitSignal?.empty_message || "暂无可用持仓裁决"}
          </div>
        ) : null}

        {!isLoading && !isError && exitSignal?.available ? (
          <div className="space-y-4">
            <section className="rounded-xl border bg-card p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge className={getExitActionBadgeClassName(exitSignal.action)}>
                  {exitSignal.action}
                </Badge>
                <Badge variant="outline">置信度 {exitSignal.confidence}</Badge>
              </div>
              <p className="mt-3 text-sm">{exitSignal.summary}</p>
              <p className="mt-2 text-muted-foreground text-sm">{exitSignal.thesis}</p>
            </section>

            <section className="rounded-xl border bg-card p-4">
              <h3 className="font-medium text-sm">利润保护视角</h3>
              <p className="mt-2 text-muted-foreground text-sm">
                {exitSignal.profit_protection_view}
              </p>
            </section>

            <section className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-xl border bg-card p-4">
                <h3 className="font-medium text-sm">证据</h3>
                <div className="mt-2 space-y-1 text-muted-foreground text-sm">
                  {exitSignal.evidence.map((item) => (
                    <p key={item}>- {item}</p>
                  ))}
                </div>
              </div>
              <div className="rounded-xl border bg-card p-4">
                <h3 className="font-medium text-sm">矛盾点</h3>
                <div className="mt-2 space-y-1 text-muted-foreground text-sm">
                  {exitSignal.disagreement.map((item) => (
                    <p key={item}>- {item}</p>
                  ))}
                </div>
              </div>
              <div className="rounded-xl border bg-card p-4">
                <h3 className="font-medium text-sm">失效条件</h3>
                <div className="mt-2 space-y-1 text-muted-foreground text-sm">
                  {exitSignal.invalid_conditions.map((item) => (
                    <p key={item}>- {item}</p>
                  ))}
                </div>
              </div>
              <div className="rounded-xl border bg-card p-4">
                <h3 className="font-medium text-sm">风控提示</h3>
                <div className="mt-2 space-y-1 text-muted-foreground text-sm">
                  {exitSignal.risk_controls.map((item) => (
                    <p key={item}>- {item}</p>
                  ))}
                </div>
              </div>
            </section>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}

export default function PortfolioOverview({
  showDailySummary = true,
  sectionTitle = "持仓处理",
  sectionDescription = "围绕已有持仓给出短周期动作建议，并支持手动维护和诊断刷新。",
  className,
}: PortfolioOverviewProps) {
  const { data, isLoading } = useGetPortfolioOverview();
  const refreshBriefing = useRefreshDailyBriefing();
  const createHolding = useCreateHolding();
  const updateHolding = useUpdateHolding();
  const deleteHolding = useDeleteHolding();
  const refreshDiagnosis = useRefreshHoldingDiagnosis();
  const { data: exitSignalList } = useGetHoldingExitSignals();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingHolding, setEditingHolding] = useState<UserHolding | null>(null);
  const [exitSignalDialogOpen, setExitSignalDialogOpen] = useState(false);
  const [selectedHolding, setSelectedHolding] = useState<UserHolding | null>(null);
  const [form, setForm] = useState<HoldingFormState>(emptyForm);

  const holdings = data?.holdings || [];
  const briefing = data?.briefing;

  const focusCount = useMemo(
    () => holdings.filter((item) => item.latest_diagnosis?.is_focus).length,
    [holdings],
  );
  const exitSignalByHoldingId = useMemo(
    () =>
      new Map(
        (exitSignalList?.items || []).map((item) => [item.holding_id, item]),
      ),
    [exitSignalList?.items],
  );

  const openCreateDialog = () => {
    setEditingHolding(null);
    setForm(emptyForm);
    setDialogOpen(true);
  };

  const openEditDialog = (holding: UserHolding) => {
    setEditingHolding(holding);
    setForm(buildFormFromHolding(holding));
    setDialogOpen(true);
  };

  const openExitSignalDialog = (holding: UserHolding) => {
    setSelectedHolding(holding);
    setExitSignalDialogOpen(true);
  };

  const handleSubmit = async () => {
    const payload = buildHoldingPayload(form);
    if (!payload) return;

    try {
      if (editingHolding) {
        await updateHolding.mutateAsync({
          holdingId: editingHolding.id,
          payload,
        });
        toast.success("持仓已更新，诊断已刷新");
      } else {
        await createHolding.mutateAsync(payload);
        toast.success("持仓已录入，首份诊断已生成");
      }
      setDialogOpen(false);
      setEditingHolding(null);
      setForm(emptyForm);
    } catch {
      toast.error("持仓保存失败");
    }
  };

  const handleDelete = async (holdingId: number) => {
    try {
      await deleteHolding.mutateAsync(holdingId);
      toast.success("持仓已删除");
    } catch {
      toast.error("删除持仓失败");
    }
  };

  const handleRefreshBriefing = async () => {
    try {
      await refreshBriefing.mutateAsync();
      toast.success("每日摘要已刷新");
    } catch {
      toast.error("每日摘要刷新失败");
    }
  };

  const handleRefreshDiagnosis = async (holdingId: number) => {
    try {
      await refreshDiagnosis.mutateAsync(holdingId);
      toast.success("持仓诊断已刷新");
    } catch {
      toast.error("持仓诊断刷新失败");
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner className="size-6" />
      </div>
    );
  }

  return (
    <div className={`flex flex-col gap-4 ${className || "p-5"}`}>
      {showDailySummary ? (
        <section className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div className="rounded-2xl border bg-background p-5">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="font-semibold text-lg">今日摘要</p>
              <p className="text-muted-foreground text-sm">
                {briefing?.summary.headline ||
                  "暂无可用摘要，补充持仓后可刷新查看。"}
              </p>
            </div>

            <Button
              variant="secondary"
              disabled={refreshBriefing.isPending}
              onClick={handleRefreshBriefing}
            >
              {refreshBriefing.isPending ? <Spinner className="size-4" /> : <RefreshCcw size={16} />}
              刷新摘要
            </Button>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            {(briefing?.summary.focus_items || []).map((item) => (
              <div
                key={`${item.type}-${item.ticker}`}
                className="rounded-xl border bg-card p-4"
              >
                <p className="font-medium text-sm">{item.title}</p>
                <p className="mt-2 text-muted-foreground text-sm">{item.summary}</p>
              </div>
            ))}

            {!briefing?.summary.focus_items?.length && (
              <div className="rounded-xl border border-dashed bg-card p-4 text-muted-foreground text-sm">
                当前暂无重点项，系统会在持仓或自选出现更明确线索后更新摘要。
              </div>
            )}
          </div>

          {!!briefing?.summary.watchlist_highlights?.length && (
            <div className="mt-4 rounded-xl border bg-card p-4">
              <div className="mb-3 flex items-center gap-2">
                <AlertTriangle className="size-4 text-orange-500" />
                <p className="font-medium text-sm">自选异动</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {briefing.summary.watchlist_highlights.map((item) => (
                  <Badge key={item.ticker} variant="secondary">
                    {item.ticker} {formatPercent(item.change_percent)}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="grid gap-3">
          <div className="rounded-2xl border bg-background p-5">
            <p className="text-muted-foreground text-sm">持仓数量</p>
            <p className="mt-2 font-semibold text-3xl">{data?.holding_count || 0}</p>
          </div>
          <div className="rounded-2xl border bg-background p-5">
            <p className="text-muted-foreground text-sm">重点关注</p>
            <p className="mt-2 font-semibold text-3xl">{focusCount}</p>
          </div>
          <div className="rounded-2xl border bg-background p-5">
            <p className="text-muted-foreground text-sm">动作汇总</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {(briefing?.summary.holding_actions || []).map((item) => (
                <Badge key={item.label} variant="secondary">
                  {item.label} {item.value}
                </Badge>
              ))}
            </div>
          </div>
        </div>
        </section>
      ) : null}

      <section className="rounded-2xl border bg-background p-5">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <p className="font-semibold text-lg">{sectionTitle}</p>
            <p className="text-muted-foreground text-sm">
              {sectionDescription}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button asChild variant="outline">
              <Link to="/home/daily-workbench">回到总控台</Link>
            </Button>
            <Button onClick={openCreateDialog}>
              <Plus size={16} />
              新增持仓
            </Button>
          </div>
        </div>

        <div className="space-y-3">
          {!holdings.length && (
            <div className="rounded-xl border border-dashed bg-card p-6 text-center text-muted-foreground text-sm">
              暂无持仓，录入后即可查看诊断、刷新摘要并形成处理建议。
            </div>
          )}

          {holdings.map((holding) => {
            const exitSignal = exitSignalByHoldingId.get(holding.id) as
              | HoldingExitSignal
              | undefined;
            return (
            <div
              key={holding.id}
              className="rounded-2xl border bg-card p-4 shadow-sm"
            >
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold text-base">
                      {holding.asset_name || holding.ticker}
                    </p>
                    <Badge variant="outline">{holding.ticker}</Badge>
                    <Badge className={getActionBadgeClassName(holding.latest_diagnosis?.action)}>
                      {holding.latest_diagnosis?.action || "待诊断"}
                    </Badge>
                    {exitSignal ? (
                      <Badge className={getExitActionBadgeClassName(exitSignal.action)}>
                        {exitSignal.action}
                      </Badge>
                    ) : null}
                    {holding.latest_diagnosis?.risk_level ? (
                      <Badge className={getRiskBadgeClassName(holding.latest_diagnosis.risk_level)}>
                        风险 {holding.latest_diagnosis.risk_level}
                      </Badge>
                    ) : null}
                  </div>

                  <div className="flex flex-wrap gap-4 text-muted-foreground text-sm">
                    <span>数量 {holding.quantity}</span>
                    <span>成本 {formatPrice(holding.cost_price)}</span>
                    <span>现价 {formatPrice(holding.market_snapshot.current_price)}</span>
                    <span
                      className={
                        (holding.market_snapshot.latest_change_percent || 0) >= 0
                          ? "text-emerald-500"
                          : "text-red-500"
                      }
                    >
                      日变动 {formatPercent(holding.market_snapshot.latest_change_percent)}
                    </span>
                    <span
                      className={
                        (holding.market_snapshot.profit_percent || 0) >= 0
                          ? "text-emerald-500"
                          : "text-red-500"
                      }
                    >
                      浮盈亏 {formatPercent(holding.market_snapshot.profit_percent)}
                    </span>
                  </div>

                  <p className="text-sm">
                    {exitSignal?.summary ||
                      holding.latest_diagnosis?.summary ||
                      "还没有诊断结果，请手动刷新。"}
                  </p>

                  {!!holding.latest_diagnosis?.reasons?.length && (
                    <ul className="space-y-1 text-muted-foreground text-sm">
                      {holding.latest_diagnosis.reasons.map((reason) => (
                        <li key={reason}>- {reason}</li>
                      ))}
                    </ul>
                  )}

                  {!!holding.thesis_note && (
                    <div className="rounded-lg bg-muted/60 p-3 text-muted-foreground text-sm">
                      <span className="font-medium text-foreground">建仓逻辑：</span>
                      {holding.thesis_note}
                    </div>
                  )}
                </div>

                <div className="flex shrink-0 items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openExitSignalDialog(holding)}
                  >
                    查看持仓裁决
                  </Button>
                  <Button
                    variant="secondary"
                    size="icon"
                    onClick={() => handleRefreshDiagnosis(holding.id)}
                    disabled={refreshDiagnosis.isPending}
                  >
                    <RefreshCcw size={16} />
                  </Button>
                  <Button
                    variant="secondary"
                    size="icon"
                    onClick={() => openEditDialog(holding)}
                  >
                    <Pencil size={16} />
                  </Button>
                  <Button
                    variant="destructive"
                    size="icon"
                    onClick={() => handleDelete(holding.id)}
                    disabled={deleteHolding.isPending}
                  >
                    <Trash2 size={16} />
                  </Button>
                </div>
              </div>

              {!!holding.latest_diagnosis?.trigger_conditions?.length && (
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <div className="rounded-xl bg-muted/40 p-3">
                    <p className="mb-2 font-medium text-sm">触发条件</p>
                    <div className="space-y-1 text-muted-foreground text-sm">
                      {holding.latest_diagnosis.trigger_conditions.map((item) => (
                        <p key={item}>- {item}</p>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-xl bg-muted/40 p-3">
                    <p className="mb-2 font-medium text-sm">失效条件</p>
                    <div className="space-y-1 text-muted-foreground text-sm">
                      {holding.latest_diagnosis.invalid_conditions.map((item) => (
                        <p key={item}>- {item}</p>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
            );
          })}
        </div>
      </section>

      <HoldingFormDialog
        open={dialogOpen}
        title={editingHolding ? "编辑持仓" : "新增持仓"}
        value={form}
        pending={createHolding.isPending || updateHolding.isPending}
        onOpenChange={setDialogOpen}
        onChange={setForm}
        onSubmit={handleSubmit}
      />
      <HoldingExitSignalDialog
        holding={selectedHolding}
        open={exitSignalDialogOpen}
        onOpenChange={setExitSignalDialogOpen}
      />
    </div>
  );
}
