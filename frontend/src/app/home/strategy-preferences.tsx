import BackButton from "@valuecell/button/back-button";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router";
import {
  useGetStrategyPreferenceProfile,
  useGetStrategyPreferenceTemplates,
  useUpdateStrategyPreferenceProfile,
} from "@/api/strategy-preference";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import type {
  StrategyPreferenceTemplate,
  UpdateStrategyPreferencePayload,
} from "@/types/strategy-preference";

const RISK_STYLE_OPTIONS = [
  { value: "steady", label: "稳健" },
  { value: "balanced", label: "均衡" },
  { value: "aggressive", label: "进攻" },
] as const;

const BUY_STYLE_OPTIONS = [
  { value: "low_absorb", label: "低吸" },
  { value: "pullback", label: "回踩" },
  { value: "breakout", label: "突破" },
  { value: "right_side", label: "右侧" },
] as const;

const buildPayloadFromTemplate = (
  template: StrategyPreferenceTemplate,
): UpdateStrategyPreferencePayload => ({
  template_id: template.template_id,
  preferred_themes: template.preferred_themes,
  holding_period_days: template.holding_period_days,
  risk_style: template.risk_style,
  buy_style: template.buy_style,
  avoid_risks: template.avoid_risks,
  accept_high_position: template.accept_high_position,
  prefer_expectation_gap: template.prefer_expectation_gap,
  prefer_leader_or_core: template.prefer_leader_or_core,
  note: template.note,
});

export default function StrategyPreferences() {
  const { data: profile, isLoading: profileLoading } = useGetStrategyPreferenceProfile();
  const { data: templates, isLoading: templatesLoading } = useGetStrategyPreferenceTemplates();
  const updateProfile = useUpdateStrategyPreferenceProfile();
  const [form, setForm] = useState<UpdateStrategyPreferencePayload | null>(null);
  const [saveState, setSaveState] = useState<"idle" | "success" | "error">("idle");

  useEffect(() => {
    if (!profile) return;
    setForm({
      template_id: profile.template_id,
      preferred_themes: profile.preferred_themes,
      holding_period_days: profile.holding_period_days,
      risk_style: profile.risk_style,
      buy_style: profile.buy_style,
      avoid_risks: profile.avoid_risks,
      accept_high_position: profile.accept_high_position,
      prefer_expectation_gap: profile.prefer_expectation_gap,
      prefer_leader_or_core: profile.prefer_leader_or_core,
      note: profile.note,
    });
  }, [profile]);

  const currentTemplate = useMemo(
    () => templates?.items.find((item) => item.template_id === form?.template_id) || null,
    [form?.template_id, templates?.items],
  );

  const saveMessage =
    saveState === "success"
      ? "已保存，机会池排序和提醒优先级会按当前偏好刷新。"
      : saveState === "error"
        ? "保存失败，请稍后重试。"
        : null;

  if (profileLoading || templatesLoading || !form) {
    return (
      <div className="flex h-full items-center justify-center bg-card">
        <Spinner className="size-5" />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-6 bg-card px-8 py-6">
      <BackButton />

      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="font-semibold text-2xl">策略偏好</h1>
          <p className="mt-1 text-muted-foreground text-sm">
            用偏好模板微调机会池排序、买点裁决和提醒优先级，但不会把系统变成激进买入指令。
          </p>
        </div>
        <Button asChild variant="outline">
          <Link to="/home/opportunities">返回机会池</Link>
        </Button>
      </div>

      <div className="rounded-2xl border bg-background p-5">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">{currentTemplate?.title || "未选择模板"}</Badge>
          <Badge variant="outline">持股周期 {form.holding_period_days} 天</Badge>
          <Badge variant="outline">
            {RISK_STYLE_OPTIONS.find((item) => item.value === form.risk_style)?.label}
          </Badge>
          <Badge variant="outline">
            {BUY_STYLE_OPTIONS.find((item) => item.value === form.buy_style)?.label}
          </Badge>
        </div>
        <p className="mt-3 text-muted-foreground text-sm">
          {currentTemplate?.summary || "当前模板主要用于保守地调整排序和提醒优先级。"}
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {templates?.items.map((template) => (
          <button
            key={template.template_id}
            type="button"
            className={`rounded-2xl border p-4 text-left transition-colors ${
              form.template_id === template.template_id
                ? "border-primary bg-primary/5"
                : "bg-background hover:bg-muted/50"
            }`}
            onClick={() => {
              setForm(buildPayloadFromTemplate(template));
              setSaveState("idle");
            }}
          >
            <div className="flex items-center justify-between gap-3">
              <p className="font-medium">{template.title}</p>
              {form.template_id === template.template_id ? (
                <Badge variant="secondary">当前选择</Badge>
              ) : null}
            </div>
            <p className="mt-2 text-muted-foreground text-sm">{template.summary}</p>
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-5 rounded-2xl border bg-background p-5">
          <div className="space-y-3">
            <Label htmlFor="preferred-themes">偏好题材</Label>
            <Input
              id="preferred-themes"
              value={form.preferred_themes.join(", ")}
              onChange={(event) => {
                setSaveState("idle");
                setForm((current) =>
                  current
                    ? {
                        ...current,
                        preferred_themes: event.target.value
                          .split(",")
                          .map((item) => item.trim())
                          .filter(Boolean),
                      }
                    : current,
                );
              }}
              placeholder="例如：AI算力, 机器人, 证券"
            />
          </div>

          <div className="space-y-3">
            <Label htmlFor="holding-period-days">持股周期天数</Label>
            <Input
              id="holding-period-days"
              type="number"
              min={1}
              max={60}
              value={form.holding_period_days}
              onChange={(event) => {
                setSaveState("idle");
                setForm((current) =>
                  current
                    ? {
                        ...current,
                        holding_period_days: Math.max(1, Number(event.target.value || 1)),
                      }
                    : current,
                );
              }}
            />
          </div>

          <div className="space-y-3">
            <Label>风险风格</Label>
            <div className="flex flex-wrap gap-2">
              {RISK_STYLE_OPTIONS.map((option) => (
                <Button
                  key={option.value}
                  type="button"
                  size="sm"
                  variant={form.risk_style === option.value ? "default" : "outline"}
                  onClick={() => {
                    setSaveState("idle");
                    setForm((current) =>
                      current ? { ...current, risk_style: option.value } : current,
                    );
                  }}
                >
                  {option.label}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <Label>买入风格</Label>
            <div className="flex flex-wrap gap-2">
              {BUY_STYLE_OPTIONS.map((option) => (
                <Button
                  key={option.value}
                  type="button"
                  size="sm"
                  variant={form.buy_style === option.value ? "default" : "outline"}
                  onClick={() => {
                    setSaveState("idle");
                    setForm((current) =>
                      current ? { ...current, buy_style: option.value } : current,
                    );
                  }}
                >
                  {option.label}
                </Button>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-5 rounded-2xl border bg-background p-5">
          <div className="flex items-center justify-between gap-3">
            <Label htmlFor="accept-high-position">接受高位追强</Label>
            <Switch
              id="accept-high-position"
              checked={form.accept_high_position}
              onCheckedChange={(checked) => {
                setSaveState("idle");
                setForm((current) =>
                  current ? { ...current, accept_high_position: checked } : current,
                );
              }}
            />
          </div>

          <div className="flex items-center justify-between gap-3">
            <Label htmlFor="prefer-expectation-gap">偏好预期差</Label>
            <Switch
              id="prefer-expectation-gap"
              checked={form.prefer_expectation_gap}
              onCheckedChange={(checked) => {
                setSaveState("idle");
                setForm((current) =>
                  current ? { ...current, prefer_expectation_gap: checked } : current,
                );
              }}
            />
          </div>

          <div className="flex items-center justify-between gap-3">
            <Label htmlFor="prefer-leader-or-core">优先龙头 / 中军</Label>
            <Switch
              id="prefer-leader-or-core"
              checked={form.prefer_leader_or_core}
              onCheckedChange={(checked) => {
                setSaveState("idle");
                setForm((current) =>
                  current ? { ...current, prefer_leader_or_core: checked } : current,
                );
              }}
            />
          </div>

          <div className="space-y-3">
            <Label htmlFor="avoid-risks">规避风险</Label>
            <Input
              id="avoid-risks"
              value={form.avoid_risks.join(", ")}
              onChange={(event) => {
                setSaveState("idle");
                setForm((current) =>
                  current
                    ? {
                        ...current,
                        avoid_risks: event.target.value
                          .split(",")
                          .map((item) => item.trim())
                          .filter(Boolean),
                      }
                    : current,
                );
              }}
              placeholder="例如：ST, 流动性风险, 退潮题材"
            />
          </div>

          <div className="space-y-3">
            <Label htmlFor="strategy-note">补充说明</Label>
            <Textarea
              id="strategy-note"
              value={form.note}
              onChange={(event) => {
                setSaveState("idle");
                setForm((current) =>
                  current ? { ...current, note: event.target.value } : current,
                );
              }}
              placeholder="例如：更重视低位承接，不接受追高。"
            />
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Button
          onClick={async () => {
            if (!form) return;
            setSaveState("idle");
            try {
              await updateProfile.mutateAsync(form);
              setSaveState("success");
            } catch {
              setSaveState("error");
            }
          }}
          disabled={updateProfile.isPending}
        >
          {updateProfile.isPending ? "保存中..." : "保存偏好"}
        </Button>
        {saveMessage ? (
          <p
            className={`text-sm ${
              saveState === "error" ? "text-red-500" : "text-muted-foreground"
            }`}
          >
            {saveMessage}
          </p>
        ) : null}
      </div>
    </div>
  );
}
