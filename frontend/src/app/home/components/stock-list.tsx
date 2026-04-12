import { Activity, Eye, ShieldAlert, TrendingUp } from "lucide-react";
import { memo, useMemo, useState } from "react";
import { Link, useLocation } from "react-router";
import { useGetHomepageContext } from "@/api/homepage-context";
import { useGetStockPrice, useGetWatchlist } from "@/api/stock";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Stock } from "@/types/stock";

const formatPercent = (value?: number | null) => {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
};

const getStatusClassName = (status?: string) => {
  if (status === "重点观察") return "bg-emerald-500/10 text-emerald-500";
  if (status === "风险观察") return "bg-red-500/10 text-red-500";
  if (status === "主题联动") return "bg-blue-500/10 text-blue-500";
  if (status === "波动观察") return "bg-orange-500/10 text-orange-500";
  return "bg-muted text-muted-foreground";
};

const getStatusIcon = (status?: string) => {
  if (status === "重点观察") return <TrendingUp className="size-4" />;
  if (status === "风险观察") return <ShieldAlert className="size-4" />;
  if (status === "主题联动") return <Activity className="size-4" />;
  return <Eye className="size-4" />;
};

function StockList() {
  const { pathname } = useLocation();
  const { data: stockList } = useGetWatchlist();
  const { data: homepageContext } = useGetHomepageContext();
  const [dialogOpen, setDialogOpen] = useState(false);

  const stockData = useMemo(() => {
    return stockList?.flatMap((group) => group.items) ?? [];
  }, [stockList]);

  const observedStocks = homepageContext?.watchlist_observation.items || [];
  const allObservedStocks =
    homepageContext?.watchlist_observation.all_items || observedStocks;
  const compactObservedStocks = allObservedStocks.slice(0, 3);

  const stockTicker = pathname.split("/")[3];

  const WatchlistFallbackItem = ({ stock }: { stock: Stock }) => {
    const { data: stockPrice } = useGetStockPrice({ ticker: stock.ticker });

    return (
      <Link
        to={`/home/stock/${stock.ticker}`}
        replace={!!stockTicker}
        className={`block rounded-xl border p-3 transition-colors hover:bg-muted/50 ${
          stockTicker === stock.ticker ? "border-primary" : "border-border"
        }`}
      >
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="font-medium text-sm">{stock.display_name}</p>
            <p className="text-muted-foreground text-xs">{stock.ticker}</p>
          </div>
          <div className="text-right">
            <p className="font-medium text-sm">{stockPrice?.price_formatted || "--"}</p>
            <p
              className={`text-xs ${
                (stockPrice?.change_percent || 0) >= 0
                  ? "text-emerald-500"
                  : "text-red-500"
              }`}
            >
              {formatPercent(stockPrice?.change_percent)}
            </p>
          </div>
        </div>
        <p className="mt-2 text-muted-foreground text-xs">常规跟踪，等待更多线索确认。</p>
      </Link>
    );
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b px-5 py-4">
        <p className="font-semibold text-base">自选观察</p>
        <p className="mt-1 text-muted-foreground text-sm">
          右侧只保留重点观察，完整列表按需展开查看。
        </p>
      </div>

      <div className="scroll-container flex-1 space-y-3 px-5 py-4">
        {compactObservedStocks.length > 0
          ? compactObservedStocks.map((stock) => (
              <Link
                key={stock.ticker}
                to={`/home/stock/${stock.ticker}`}
                replace={!!stockTicker}
                className={`block rounded-2xl border bg-background p-4 transition-colors hover:bg-muted/50 ${
                  stockTicker === stock.ticker ? "border-primary" : "border-border"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{stock.display_name}</span>
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ${getStatusClassName(stock.status)}`}
                      >
                        {getStatusIcon(stock.status)}
                        {stock.status}
                      </span>
                    </div>
                    <p className="text-muted-foreground text-xs">{stock.ticker}</p>
                  </div>

                  <div className="text-right">
                    <p className="font-medium text-sm">{stock.price || "--"}</p>
                    <p
                      className={`text-xs ${
                        (stock.change_percent || 0) >= 0
                          ? "text-emerald-500"
                          : "text-red-500"
                      }`}
                    >
                      {formatPercent(stock.change_percent)}
                    </p>
                  </div>
                </div>

                <p className="mt-3 text-sm">{stock.reason}</p>

                <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                  <span>{stock.tradeability_state}</span>
                  <span>· 预期差 {stock.expectation_gap_level}</span>
                  <span>· {stock.watchlist_name}</span>
                </div>
              </Link>
            ))
          : stockData.map((stock) => (
              <WatchlistFallbackItem key={stock.ticker} stock={stock} />
            ))}

        {!observedStocks.length && !stockData.length ? (
          <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
            暂无自选股，添加后可在这里查看观察状态、涨跌变化和关注理由。
          </div>
        ) : null}

        {allObservedStocks.length > 3 || stockData.length > 3 ? (
          <Button variant="secondary" className="w-full" onClick={() => setDialogOpen(true)}>
            查看全部自选观察
          </Button>
        ) : null}
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-h-[80vh] overflow-hidden sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>全部自选观察</DialogTitle>
          </DialogHeader>
          <div className="scroll-container space-y-3 pr-1">
            {allObservedStocks.length > 0
              ? allObservedStocks.map((stock) => (
                  <Link
                    key={`dialog-${stock.ticker}`}
                    to={`/home/stock/${stock.ticker}`}
                    replace={!!stockTicker}
                    className="block rounded-2xl border bg-background p-4 transition-colors hover:bg-muted/50"
                    onClick={() => setDialogOpen(false)}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">{stock.display_name}</span>
                          <span
                            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ${getStatusClassName(stock.status)}`}
                          >
                            {getStatusIcon(stock.status)}
                            {stock.status}
                          </span>
                        </div>
                        <p className="text-muted-foreground text-xs">{stock.ticker}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-sm">{stock.price || "--"}</p>
                        <p
                          className={`text-xs ${
                            (stock.change_percent || 0) >= 0
                              ? "text-emerald-500"
                              : "text-red-500"
                          }`}
                        >
                          {formatPercent(stock.change_percent)}
                        </p>
                      </div>
                    </div>

                    <p className="mt-3 text-sm">{stock.reason}</p>

                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                      <span>{stock.tradeability_state}</span>
                      <span>· 预期差 {stock.expectation_gap_level}</span>
                      <span>· {stock.watchlist_name}</span>
                    </div>
                  </Link>
                ))
              : stockData.map((stock) => (
                  <WatchlistFallbackItem key={`dialog-${stock.ticker}`} stock={stock} />
                ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default memo(StockList);
