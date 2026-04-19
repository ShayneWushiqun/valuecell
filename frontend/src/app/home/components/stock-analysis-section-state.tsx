import { AlertCircle, RefreshCw } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

type StockAnalysisSectionStateProps = {
  title: string;
  loadingText: string;
  emptyText?: string;
  errorText?: string;
  isLoading?: boolean;
  isRefreshing?: boolean;
  hasData?: boolean;
  isError?: boolean;
  onRetry?: () => void;
};

export function StockAnalysisSectionState({
  title,
  loadingText,
  emptyText,
  errorText,
  isLoading = false,
  isRefreshing = false,
  hasData = true,
  isError = false,
  onRetry,
}: StockAnalysisSectionStateProps) {
  if (isLoading && !hasData) {
    return (
      <div className="rounded-xl border border-dashed p-4">
        <p className="mb-3 font-medium text-sm">{loadingText}</p>
        <div className="space-y-2">
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
        </div>
      </div>
    );
  }

  if (isError && !hasData) {
    return (
      <Alert variant="destructive" className="rounded-xl">
        <AlertCircle />
        <AlertTitle>{title}加载失败</AlertTitle>
        <AlertDescription>
          <p>{errorText || `${title}暂时不可用，请稍后再试。`}</p>
          {onRetry ? (
            <Button size="sm" variant="outline" onClick={onRetry}>
              重试
            </Button>
          ) : null}
        </AlertDescription>
      </Alert>
    );
  }

  if (!hasData && emptyText) {
    return (
      <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
        {emptyText}
      </div>
    );
  }

  if (hasData && isRefreshing) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-dashed px-3 py-2 text-muted-foreground text-xs">
        <RefreshCw className="size-3.5 animate-spin" />
        已展示上次结果，正在后台刷新{title}
      </div>
    );
  }

  return null;
}
