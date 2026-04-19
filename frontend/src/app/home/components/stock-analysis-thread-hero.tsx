import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

type StockAnalysisThreadHeroProps = {
  title: string;
  focusType?: string | null;
  tickers: string[];
  themes: string[];
  threadHealthStatus?: string | null;
  threadHealthScore?: number | null;
  nextAction?: string | null;
  nextActionReason?: string | null;
  onAddTicker: (ticker: string) => void;
  onAddTheme: (theme: string) => void;
};

export function StockAnalysisThreadHero({
  title,
  focusType,
  tickers,
  themes,
  threadHealthStatus,
  threadHealthScore,
  nextAction,
  nextActionReason,
  onAddTicker,
  onAddTheme,
}: StockAnalysisThreadHeroProps) {
  const primaryFocus =
    tickers[0] || themes[0] || (focusType === "mixed" ? "多对象研究" : "待明确");

  return (
    <div className="rounded-2xl border bg-muted/20 p-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="font-semibold text-xl">{title}</h2>
            {focusType ? <Badge variant="secondary">{focusType}</Badge> : null}
            {threadHealthStatus ? (
              <Badge variant="outline">
                线程状态 {threadHealthStatus}
                {typeof threadHealthScore === "number" ? ` · ${threadHealthScore}` : ""}
              </Badge>
            ) : null}
          </div>
          <p className="text-muted-foreground text-sm">
            当前主研究对象：{primaryFocus}
            {tickers.length > 1 ? ` · ${tickers.length} 个标的` : ""}
            {themes.length ? ` · ${themes.length} 个主题` : ""}
          </p>
          {nextAction ? (
            <div className="rounded-lg border border-dashed bg-background/80 px-3 py-2">
              <p className="font-medium text-sm">当前最建议动作：{nextAction}</p>
              <p className="mt-1 text-muted-foreground text-xs">
                {nextActionReason || "建议优先按这个方向继续研究。"}
              </p>
            </div>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2 lg:max-w-sm lg:justify-end">
          {tickers.map((ticker) => (
            <Button
              key={ticker}
              size="sm"
              variant="outline"
              onClick={() => onAddTicker(ticker)}
            >
              {ticker}
            </Button>
          ))}
          {themes.map((theme) => (
            <Button
              key={theme}
              size="sm"
              variant="outline"
              onClick={() => onAddTheme(theme)}
            >
              {theme}
            </Button>
          ))}
        </div>
      </div>
      <p className="mt-3 text-muted-foreground text-xs">
        点击右侧标的或主题，可直接加入当前对比对象。
      </p>
    </div>
  );
}
