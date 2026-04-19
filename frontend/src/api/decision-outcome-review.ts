import { useQuery } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type { DecisionOutcomeReviewList } from "@/types/decision-outcome-review";

export const useGetDecisionOutcomeReviews = ({
  limit = 60,
  outcomeStatus,
  action,
  reviewHorizonDays,
  enabled = true,
}: {
  limit?: number;
  outcomeStatus?: string;
  action?: string;
  reviewHorizonDays?: number;
  enabled?: boolean;
}) => {
  const queryString = [
    `limit=${limit}`,
    outcomeStatus
      ? `outcome_status=${encodeURIComponent(outcomeStatus)}`
      : null,
    action ? `action=${encodeURIComponent(action)}` : null,
    reviewHorizonDays ? `review_horizon_days=${reviewHorizonDays}` : null,
  ]
    .filter(Boolean)
    .join("&");

  return useQuery({
    queryKey: API_QUERY_KEYS.DECISION_OUTCOME_REVIEW.list(
      `${outcomeStatus || "all"}:${action || "all"}:${reviewHorizonDays || 0}:${limit}`,
    ),
    enabled,
    queryFn: () =>
      apiClient.get<ApiResponse<DecisionOutcomeReviewList>>(
        `decision-outcome-reviews?${queryString}`,
      ),
    select: (response) => response.data,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  });
};
