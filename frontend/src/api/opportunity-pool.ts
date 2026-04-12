import { useQuery } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type { OpportunityPool } from "@/types/opportunity-pool";

export const useGetOpportunityCandidates = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.OPPORTUNITY_POOL.candidates,
    queryFn: () =>
      apiClient.get<ApiResponse<OpportunityPool>>("opportunities/candidates"),
    select: (response) => response.data,
  });
