import { useQuery } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type { DecisionEffectivenessSummary } from "@/types/decision-effectiveness";

export const useGetDecisionEffectivenessSummary = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.DECISION_EFFECTIVENESS.summary,
    queryFn: () =>
      apiClient.get<ApiResponse<DecisionEffectivenessSummary>>(
        "decision-effectiveness/summary",
      ),
    select: (response) => response.data,
  });
