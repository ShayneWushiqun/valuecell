import { ChevronDown, History, Loader2 } from "lucide-react";
import { type FC, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { useGetModelProviderDetail, useGetSortedModelProviders } from "@/api/setting";
import {
  useCreateTradingAgentsRun,
  useGetTradingAgentsRun,
  useGetTradingAgentsRuns,
} from "@/api/tradingagents";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import MarkdownRenderer from "@/components/valuecell/renderer/markdown-renderer";
import { cn } from "@/lib/utils";
import type { AgentViewProps } from "@/types/agent";
import type {
  TradingAgentsAnalyst,
  TradingAgentsRunRequest,
  TradingAgentsRunResult,
} from "@/types/tradingagents";

const SUPPORTED_PROVIDERS = [
  "openai",
  "google",
  "openrouter",
  "ollama",
  "openai-compatible",
  "siliconflow",
  "deepseek",
  "dashscope",
] as const;

const ANALYST_OPTIONS: Array<{
  value: TradingAgentsAnalyst;
  label: string;
}> = [
  { value: "market", label: "Market" },
  { value: "social", label: "Social" },
  { value: "news", label: "News" },
  { value: "fundamentals", label: "Fundamentals" },
];

const OUTPUT_LANGUAGE_OPTIONS = [
  { value: "Chinese", label: "中文" },
  { value: "English", label: "English" },
  { value: "Japanese", label: "日本語" },
];

const RESIZABLE_CARD_CLASS =
  "min-h-[240px] max-h-[720px] [resize:vertical] overflow-hidden";
const RESIZABLE_HERO_CARD_CLASS =
  "min-h-[280px] max-h-[760px] [resize:vertical] overflow-hidden";
const RESIZABLE_SECTION_CARD_CLASS =
  "min-h-[320px] max-h-[820px] [resize:vertical] overflow-hidden";

function getDefaultOutputLanguage(language: string): string {
  if (language.startsWith("zh")) return "Chinese";
  if (language.startsWith("ja")) return "Japanese";
  return "English";
}

function getStatusVariant(status?: TradingAgentsRunResult["status"]) {
  if (status === "failed") return "destructive";
  if (status === "succeeded") return "secondary";
  return "outline";
}

function formatTimestamp(
  value: string | null | undefined,
  language: string,
): string {
  if (!value) return "--";
  return new Date(value).toLocaleString(language);
}

function getStatusLabel(
  status: TradingAgentsRunResult["status"] | undefined,
  t: (key: string) => string,
): string {
  if (!status) return t("tradingagents.status.idle");
  return t(`tradingagents.status.${status}`);
}

function getProgressText(
  isPending: boolean,
  result: TradingAgentsRunResult | null,
  t: (key: string) => string,
): string {
  if (isPending) return t("tradingagents.progress.creating");
  if (!result) return t("tradingagents.progress.idle");
  if (result.status === "queued") return t("tradingagents.progress.queued");
  if (result.status === "running") return result.progress_message || t("tradingagents.progress.running");
  if (result.status === "failed") return result.error_message || t("tradingagents.status.failed");
  return t("tradingagents.toast.completed");
}

function SummaryMarkdown({
  content,
  emptyText,
  className,
}: {
  content: string | null | undefined;
  emptyText: string;
  className?: string;
}) {
  if (!content) {
    return <div className={cn("text-muted-foreground text-sm", className)}>{emptyText}</div>;
  }

  return (
    <div className={cn("relative min-h-0 flex-1", className)}>
      <div className="scroll-container min-h-0 overflow-y-auto pr-2">
        <MarkdownRenderer
          content={content}
          className="max-w-none break-words text-muted-foreground prose-p:my-2 prose-li:my-1"
        />
      </div>
    </div>
  );
}

function getPreferredReportKey(result: TradingAgentsRunResult | null): string {
  if (!result?.reports.length) {
    return "";
  }

  const finalReport = result.reports.find((item) => item.key === "final_trade_decision");
  return finalReport?.key || result.reports[0].key;
}

const TradingAgentsArea: FC<AgentViewProps> = ({ agentName }) => {
  const { t, i18n } = useTranslation();
  const { providers = [], defaultProvider } = useGetSortedModelProviders();
  const supportedProviders = useMemo(
    () =>
      providers.filter((item) =>
        SUPPORTED_PROVIDERS.includes(item.provider as (typeof SUPPORTED_PROVIDERS)[number]),
      ),
    [providers],
  );

  const [form, setForm] = useState<TradingAgentsRunRequest>({
    symbol: "",
    trade_date: new Date().toISOString().slice(0, 10),
    provider: "",
    deep_model: "",
    quick_model: "",
    output_language: getDefaultOutputLanguage(i18n.language),
    analysts: ["market", "social", "news", "fundamentals"],
    debug: false,
  });
  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [selectedReportKey, setSelectedReportKey] = useState<string>("");
  const [historyOpen, setHistoryOpen] = useState(false);
  const [runDialogOpen, setRunDialogOpen] = useState(false);

  useEffect(() => {
    setForm((current) => ({
      ...current,
      output_language: current.output_language || getDefaultOutputLanguage(i18n.language),
    }));
  }, [i18n.language]);

  useEffect(() => {
    if (form.provider) return;
    const preferred =
      supportedProviders.find((item) => item.provider === defaultProvider)?.provider ||
      supportedProviders[0]?.provider ||
      "";
    if (!preferred) return;
    setForm((current) => ({
      ...current,
      provider: preferred,
    }));
  }, [defaultProvider, form.provider, supportedProviders]);

  const { data: providerDetail } = useGetModelProviderDetail(form.provider || undefined);
  const createRun = useCreateTradingAgentsRun();
  const { data: runList } = useGetTradingAgentsRuns();
  const { data: runDetail } = useGetTradingAgentsRun(selectedRunId || undefined);

  const selectedRun = useMemo(
    () =>
      runDetail ||
      runList?.runs.find((item) => item.run_id === selectedRunId) ||
      null,
    [runDetail, runList?.runs, selectedRunId],
  );

  useEffect(() => {
    const defaultModel =
      providerDetail?.default_model_id || providerDetail?.models?.[0]?.model_id || "";
    if (!defaultModel) return;
    setForm((current) => ({
      ...current,
      deep_model: defaultModel,
      quick_model: defaultModel,
    }));
  }, [providerDetail?.default_model_id, providerDetail?.models]);

  useEffect(() => {
    if (!runList?.runs.length) return;
    const hasSelectedRun = runList.runs.some((item) => item.run_id === selectedRunId);
    if (hasSelectedRun) return;
    const preferredRun =
      runList.runs.find((item) => item.status === "running" || item.status === "queued") ||
      runList.runs[0];
    if (preferredRun) {
      setSelectedRunId(preferredRun.run_id);
    }
  }, [runList?.runs, selectedRunId]);

  useEffect(() => {
    if (!selectedRun?.reports.length) {
      setSelectedReportKey("");
      return;
    }

    setSelectedReportKey(getPreferredReportKey(selectedRun));
  }, [selectedRun?.run_id]);

  useEffect(() => {
    if (!selectedRun?.reports.length) {
      return;
    }

    const preferredReportKey = getPreferredReportKey(selectedRun);
    const hasCurrentReport = selectedRun.reports.some((item) => item.key === selectedReportKey);
    if (!hasCurrentReport) {
      setSelectedReportKey(preferredReportKey);
    }
  }, [selectedReportKey, selectedRun?.reports, selectedRun]);

  const selectedReport =
    selectedRun?.reports.find((item) => item.key === selectedReportKey) || null;
  const finalDecisionReport =
    selectedRun?.reports.find((item) => item.key === "final_trade_decision") || null;

  const handleChange = <K extends keyof TradingAgentsRunRequest,>(
    key: K,
    value: TradingAgentsRunRequest[K],
  ) => {
    setForm((current) => ({
      ...current,
      [key]: value,
    }));
  };

  const handleToggleAnalyst = (analyst: TradingAgentsAnalyst) => {
    setForm((current) => {
      const nextAnalysts = current.analysts.includes(analyst)
        ? current.analysts.filter((item) => item !== analyst)
        : [...current.analysts, analyst];
      return {
        ...current,
        analysts: nextAnalysts,
      };
    });
  };

  const handleSubmit = async () => {
    if (!form.symbol.trim()) {
      toast.error(t("tradingagents.toast.symbolRequired"));
      return;
    }
    if (!form.trade_date) {
      toast.error(t("tradingagents.toast.dateRequired"));
      return;
    }
    if (!form.deep_model || !form.quick_model) {
      toast.error(t("tradingagents.toast.modelRequired"));
      return;
    }
    if (!form.analysts.length) {
      toast.error(t("tradingagents.toast.analystRequired"));
      return;
    }

    try {
      const response = await createRun.mutateAsync(form);
      setSelectedRunId(response.data.run_id);
      setRunDialogOpen(false);
      toast.success(t("tradingagents.toast.runCreated"));
    } catch {
      toast.error(t("tradingagents.toast.runFailed"));
    }
  };

  return (
    <div className="flex flex-1 overflow-hidden bg-muted/30">
      <div className="scroll-container flex flex-1 flex-col gap-4 overflow-y-auto p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <h2 className="font-semibold text-2xl">
                {selectedRun?.symbol || t("tradingagents.title")}
              </h2>
              <Badge variant={getStatusVariant(selectedRun?.status)}>
                {getStatusLabel(selectedRun?.status, t)}
              </Badge>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-muted-foreground text-sm">
              <span>
                {t("tradingagents.meta.currentStage")}: {selectedRun?.progress_stage || "--"}
              </span>
              <span>
                {t("tradingagents.meta.lastUpdated")}:{" "}
                {formatTimestamp(selectedRun?.updated_at, i18n.language)}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Dialog open={runDialogOpen} onOpenChange={setRunDialogOpen}>
              <DialogTrigger asChild>
                <Button className="gap-2">
                  {createRun.isPending ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : null}
                  {t("tradingagents.form.open")}
                </Button>
              </DialogTrigger>
              <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
                <DialogHeader>
                  <DialogTitle>{t("tradingagents.form.title")}</DialogTitle>
                  <DialogDescription>
                    {t("tradingagents.description", { agentName })}
                  </DialogDescription>
                </DialogHeader>

                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2 flex flex-col gap-2">
                    <span className="font-medium text-sm">
                      {t("tradingagents.form.symbol")}
                    </span>
                    <Input
                      value={form.symbol}
                      onChange={(event) =>
                        handleChange("symbol", event.target.value.toUpperCase())
                      }
                      placeholder="000988.SZ"
                    />
                  </div>

                  <div className="col-span-1 flex flex-col gap-2">
                    <span className="font-medium text-sm">
                      {t("tradingagents.form.tradeDate")}
                    </span>
                    <Input
                      type="date"
                      value={form.trade_date}
                      onChange={(event) => handleChange("trade_date", event.target.value)}
                    />
                  </div>

                  <div className="col-span-1 flex flex-col gap-2">
                    <span className="font-medium text-sm">
                      {t("tradingagents.form.outputLanguage")}
                    </span>
                    <Select
                      value={form.output_language}
                      onValueChange={(value) => handleChange("output_language", value)}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder={t("tradingagents.form.outputLanguage")} />
                      </SelectTrigger>
                      <SelectContent>
                        {OUTPUT_LANGUAGE_OPTIONS.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="col-span-2 flex flex-col gap-2">
                    <span className="font-medium text-sm">
                      {t("tradingagents.form.provider")}
                    </span>
                    <Select
                      value={form.provider}
                      onValueChange={(value) => handleChange("provider", value)}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder={t("tradingagents.form.provider")} />
                      </SelectTrigger>
                      <SelectContent>
                        {supportedProviders.map(({ provider }) => (
                          <SelectItem key={provider} value={provider}>
                            {t(`strategy.providers.${provider}`) || provider}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="col-span-1 flex flex-col gap-2">
                    <span className="font-medium text-sm">
                      {t("tradingagents.form.deepModel")}
                    </span>
                    <Select
                      value={form.deep_model}
                      onValueChange={(value) => handleChange("deep_model", value)}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder={t("tradingagents.form.deepModel")} />
                      </SelectTrigger>
                      <SelectContent>
                        {(providerDetail?.models || []).map((model) => (
                          <SelectItem key={model.model_id} value={model.model_id}>
                            {model.model_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="col-span-1 flex flex-col gap-2">
                    <span className="font-medium text-sm">
                      {t("tradingagents.form.quickModel")}
                    </span>
                    <Select
                      value={form.quick_model}
                      onValueChange={(value) => handleChange("quick_model", value)}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder={t("tradingagents.form.quickModel")} />
                      </SelectTrigger>
                      <SelectContent>
                        {(providerDetail?.models || []).map((model) => (
                          <SelectItem key={model.model_id} value={model.model_id}>
                            {model.model_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="col-span-2 flex flex-col gap-3">
                    <span className="font-medium text-sm">
                      {t("tradingagents.form.analysts")}
                    </span>
                    <div className="grid grid-cols-2 gap-3">
                      {ANALYST_OPTIONS.map((option) => (
                        <label
                          key={option.value}
                          className="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm"
                        >
                          <Checkbox
                            checked={form.analysts.includes(option.value)}
                            onCheckedChange={() => handleToggleAnalyst(option.value)}
                          />
                          <span>{option.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="col-span-2">
                    <label className="flex items-start gap-3 rounded-lg border px-3 py-3">
                      <Checkbox
                        checked={form.debug}
                        onCheckedChange={(checked) =>
                          handleChange("debug", checked === true)
                        }
                      />
                      <div className="flex flex-col gap-1">
                        <span className="font-medium text-sm">
                          {t("tradingagents.form.debug")}
                        </span>
                        <span className="text-muted-foreground text-xs">
                          {t("tradingagents.form.debugDescription")}
                        </span>
                      </div>
                    </label>
                  </div>
                </div>

                <div className="flex justify-end gap-3">
                  <Button
                    className="min-w-36"
                    disabled={createRun.isPending}
                    onClick={handleSubmit}
                  >
                    {createRun.isPending ? (
                      <span className="flex items-center gap-2">
                        <Loader2 className="size-4 animate-spin" />
                        {t("tradingagents.form.currentRun")}
                      </span>
                    ) : (
                      t("tradingagents.form.run")
                    )}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>

            <Popover open={historyOpen} onOpenChange={setHistoryOpen}>
              <PopoverTrigger asChild>
                <Button variant="outline" className="shrink-0 gap-2">
                  <History className="size-4" />
                  {t("tradingagents.history.title")}
                  <Badge variant="secondary">{runList?.runs.length || 0}</Badge>
                  <ChevronDown className="size-4 text-muted-foreground" />
                </Button>
              </PopoverTrigger>
              <PopoverContent align="end" className="w-96 p-0">
                <div className="border-b px-4 py-3">
                  <div className="font-medium text-sm">{t("tradingagents.history.title")}</div>
                  <div className="text-muted-foreground text-xs">
                    {runList?.running_count || 0} running
                  </div>
                </div>
                <div className="max-h-[420px] space-y-2 overflow-y-auto p-3">
                  {runList?.runs.length ? (
                    runList.runs.map((run) => (
                      <button
                        type="button"
                        key={run.run_id}
                        onClick={() => {
                          setSelectedRunId(run.run_id);
                          setHistoryOpen(false);
                        }}
                        className={cn(
                          "w-full rounded-xl border bg-card px-4 py-4 text-left transition-colors hover:bg-muted/60",
                          selectedRunId === run.run_id && "border-primary bg-primary/5",
                        )}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="min-w-0">
                            <div className="truncate font-medium text-sm">{run.symbol}</div>
                            <div className="mt-1 text-muted-foreground text-xs">
                              {formatTimestamp(run.created_at, i18n.language)}
                            </div>
                          </div>
                          <Badge variant={getStatusVariant(run.status)}>
                            {getStatusLabel(run.status, t)}
                          </Badge>
                        </div>
                        <div className="mt-3 line-clamp-2 text-muted-foreground text-xs">
                          {run.decision_signal ||
                            run.summary?.final_decision ||
                            run.progress_message ||
                            "--"}
                        </div>
                        <div className="mt-3 flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">
                            {run.progress_stage || "--"}
                          </span>
                          <span className="font-medium text-primary">
                            {t("tradingagents.history.detail")}
                          </span>
                        </div>
                      </button>
                    ))
                  ) : (
                    <div className="rounded-xl border bg-card px-4 py-6 text-muted-foreground text-sm">
                      {t("tradingagents.history.empty")}
                    </div>
                  )}
                </div>
              </PopoverContent>
            </Popover>
          </div>
        </div>

        <div className="grid shrink-0 grid-cols-1 gap-4 xl:grid-cols-12">
          <Card className={cn("gap-2 py-4 xl:col-span-4", RESIZABLE_CARD_CLASS)}>
            <CardHeader className="px-4">
              <CardTitle className="text-base">
                {t("tradingagents.progress.title")}
              </CardTitle>
            </CardHeader>
            <CardContent className="scroll-container flex flex-col gap-3 overflow-y-auto px-4 text-sm">
              <div className="flex items-center justify-between gap-3">
                <Badge variant={getStatusVariant(selectedRun?.status)}>
                  {getStatusLabel(selectedRun?.status, t)}
                </Badge>
                <span className="text-muted-foreground text-xs">
                  {selectedRun?.progress_percent ?? 0}%
                </span>
              </div>
              <div className="text-muted-foreground">
                {getProgressText(createRun.isPending, selectedRun, t)}
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs text-muted-foreground">
                <div className="rounded-lg border bg-muted/30 px-3 py-2">
                  <div className="font-medium text-foreground">
                    {t("tradingagents.meta.lastUpdated")}
                  </div>
                  <div>{formatTimestamp(selectedRun?.updated_at, i18n.language)}</div>
                </div>
                <div className="rounded-lg border bg-muted/30 px-3 py-2">
                  <div className="font-medium text-foreground">
                    {t("tradingagents.meta.currentStage")}
                  </div>
                  <div>{selectedRun?.progress_stage || "--"}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={cn("gap-2 py-4 xl:col-span-4", RESIZABLE_CARD_CLASS)}>
            <CardHeader className="px-4">
              <CardTitle className="text-base">
                {t("tradingagents.logs.title")}
              </CardTitle>
            </CardHeader>
            <CardContent className="scroll-container flex flex-col gap-2 overflow-y-auto px-4 text-sm">
              {selectedRun?.step_logs.length ? (
                selectedRun.step_logs.slice(-3).map((log) => (
                  <div key={`${log.stage}-${log.created_at}`} className="rounded-lg border px-3 py-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium">{log.title}</span>
                      <span className="text-muted-foreground text-xs">
                        {formatTimestamp(log.created_at, i18n.language)}
                      </span>
                    </div>
                    <div className="mt-1 text-muted-foreground text-xs">{log.message}</div>
                  </div>
                ))
              ) : (
                <div className="text-muted-foreground">
                  {t("tradingagents.logs.empty")}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className={cn("gap-2 py-4 xl:col-span-4", RESIZABLE_HERO_CARD_CLASS)}>
            <CardHeader className="px-4">
              <CardTitle className="text-base">
                {t("tradingagents.coreSummary.finalDecision")}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex h-full min-h-0 flex-col gap-3 px-4 text-sm">
              <div className="break-words font-semibold text-2xl">
                {selectedRun?.decision_signal || t("tradingagents.coreSummary.empty")}
              </div>
              <SummaryMarkdown
                content={
                  finalDecisionReport?.content ||
                  selectedRun?.summary?.final_decision ||
                  selectedRun?.progress_message
                }
                emptyText={t("tradingagents.coreSummary.empty")}
              />
            </CardContent>
          </Card>
        </div>

        <div className="flex flex-col gap-4">
          <div className="flex flex-col items-stretch gap-4 xl:flex-row">
            <Card className={cn("w-full shrink-0 gap-3 py-4 xl:w-72", RESIZABLE_SECTION_CARD_CLASS)}>
              <CardHeader className="px-4">
                <CardTitle className="text-base">
                  {t("tradingagents.reports.title")}
                </CardTitle>
              </CardHeader>
              <CardContent className="scroll-container flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto px-4">
                {selectedRun?.reports.length ? (
                  selectedRun.reports.map((report) => (
                    <button
                      type="button"
                      key={report.key}
                      onClick={() => setSelectedReportKey(report.key)}
                      className={`rounded-lg border px-3 py-3 text-left text-sm transition-colors ${
                        selectedReportKey === report.key
                          ? "border-primary bg-primary/5"
                          : "hover:bg-muted"
                      }`}
                    >
                      <div className="font-medium">{report.title}</div>
                      <div className="mt-1 text-muted-foreground text-xs">
                        {t("tradingagents.history.detail")}
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="text-muted-foreground text-sm">
                    {t("tradingagents.reports.empty")}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className={cn("flex-1 gap-3 py-4", RESIZABLE_SECTION_CARD_CLASS)}>
              <CardHeader className="px-4">
                <CardTitle className="text-base">
                  {selectedReport?.title || t("tradingagents.reportViewer.placeholderTitle")}
                </CardTitle>
              </CardHeader>
              <CardContent className="scroll-container min-h-0 flex-1 overflow-y-auto px-4">
                {selectedReport ? (
                  <MarkdownRenderer content={selectedReport.content} />
                ) : (
                  <div className="text-muted-foreground text-sm">
                    {selectedRun
                      ? t("tradingagents.reportViewer.placeholder")
                      : t("tradingagents.empty")}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <Card className={cn("gap-3 py-4", RESIZABLE_SECTION_CARD_CLASS)}>
            <CardHeader className="px-4">
              <CardTitle className="text-base">
                {t("tradingagents.timeline.title")}
              </CardTitle>
            </CardHeader>
            <CardContent className="scroll-container grid min-h-0 flex-1 grid-cols-1 gap-3 overflow-y-auto px-4 lg:grid-cols-2">
              {selectedRun?.step_logs.length ? (
                selectedRun.step_logs.map((log) => (
                  <div key={`${log.stage}-${log.created_at}`} className="rounded-lg border px-3 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "size-2 rounded-full bg-muted-foreground/40",
                            log.level === "running" && "bg-blue-500",
                            log.level === "completed" && "bg-green-500",
                            log.level === "warning" && "bg-yellow-500",
                            log.level === "error" && "bg-red-500",
                          )}
                        />
                        <span className="font-medium text-sm">{log.title}</span>
                      </div>
                      <span className="text-muted-foreground text-xs">
                        {log.progress_percent ?? "--"}%
                      </span>
                    </div>
                    <div className="mt-2 text-muted-foreground text-xs">{log.message}</div>
                    <div className="mt-2 text-muted-foreground text-xs">
                      {formatTimestamp(log.created_at, i18n.language)}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-muted-foreground text-sm">
                  {t("tradingagents.timeline.empty")}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default TradingAgentsArea;
