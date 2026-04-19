import { useQuery } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type { StockAnalysisOverview } from "@/types/stock-analysis-overview";

export const useGetStockAnalysisOverview = (enabled = true) =>
  useQuery({
    queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.globalOverview,
    enabled,
    queryFn: () =>
      apiClient.get<ApiResponse<StockAnalysisOverview>>("stock-analysis/overview"),
    select: (response) => response.data,
    staleTime: 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  });
