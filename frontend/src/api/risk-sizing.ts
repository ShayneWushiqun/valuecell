import { useQuery } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type { RiskSizingSummary, RiskSizingTicker } from "@/types/risk-sizing";

export const useGetRiskSizingSummary = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.RISK_SIZING.summary,
    queryFn: () =>
      apiClient.get<ApiResponse<RiskSizingSummary>>("risk-sizing/summary"),
    select: (response) => response.data,
  });

export const useGetRiskSizingTicker = (ticker: string | null, enabled = true) =>
  useQuery({
    queryKey: API_QUERY_KEYS.RISK_SIZING.ticker(ticker || ""),
    enabled: enabled && !!ticker,
    queryFn: () =>
      apiClient.get<ApiResponse<RiskSizingTicker>>(
        `risk-sizing/ticker?ticker=${encodeURIComponent(ticker || "")}`,
      ),
    select: (response) => response.data,
  });
