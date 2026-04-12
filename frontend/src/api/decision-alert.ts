import { useQuery } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type { DecisionAlertSummary } from "@/types/decision-alert";

export const useGetDecisionAlertSummary = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.DECISION_ALERT.summary,
    queryFn: () =>
      apiClient.get<ApiResponse<DecisionAlertSummary>>("decision-alerts/summary"),
    select: (response) => response.data,
  });
