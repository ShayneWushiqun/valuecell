import { useQuery } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type { AShareDecisionContext } from "@/types/ashare-decision-context";

export const useGetAShareDecisionContext = (
  ticker: string,
  enabled = true,
) =>
  useQuery({
    queryKey: API_QUERY_KEYS.ASHARE_DECISION_CONTEXT.context(ticker),
    enabled: enabled && !!ticker,
    queryFn: () =>
      apiClient.get<ApiResponse<AShareDecisionContext>>(
        `ashare-decision/context?ticker=${encodeURIComponent(ticker)}`,
      ),
    select: (response) => response.data,
  });
