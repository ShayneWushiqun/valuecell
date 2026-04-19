import { useQuery } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  HoldingLifecycleDetail,
  HoldingLifecycleOverview,
} from "@/types/holding-lifecycle";

export const useGetHoldingLifecycleOverview = (enabled = true) =>
  useQuery({
    queryKey: API_QUERY_KEYS.HOLDING_LIFECYCLE.overview,
    enabled,
    queryFn: () =>
      apiClient.get<ApiResponse<HoldingLifecycleOverview>>(
        "holding-lifecycle/overview",
      ),
    select: (response) => response.data,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  });

export const useGetHoldingLifecycleDetail = (
  holdingId: number | null,
  enabled = true,
) =>
  useQuery({
    queryKey: API_QUERY_KEYS.HOLDING_LIFECYCLE.detail(holdingId || 0),
    enabled: enabled && !!holdingId,
    queryFn: () =>
      apiClient.get<ApiResponse<HoldingLifecycleDetail>>(
        `holding-lifecycle/holdings/${holdingId}`,
      ),
    select: (response) => response.data,
  });
