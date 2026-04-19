import { useQuery } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type { OpportunityPool } from "@/types/opportunity-pool";

export const useGetOpportunityCandidates = (enabled = true) =>
  useQuery({
    queryKey: API_QUERY_KEYS.OPPORTUNITY_POOL.candidates,
    enabled,
    queryFn: () =>
      apiClient.get<ApiResponse<OpportunityPool>>("opportunities/candidates"),
    select: (response) => response.data,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  });
