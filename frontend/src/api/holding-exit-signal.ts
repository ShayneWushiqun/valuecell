import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  HoldingExitSignal,
  HoldingExitSignalList,
} from "@/types/holding-exit-signal";

export const useGetHoldingExitSignals = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.PORTFOLIO.exitSignals,
    queryFn: () =>
      apiClient.get<ApiResponse<HoldingExitSignalList>>("portfolio/exit-signals"),
    select: (response) => response.data,
  });

export const useGetHoldingExitSignal = (holdingId: number | null, enabled = true) =>
  useQuery({
    queryKey: API_QUERY_KEYS.PORTFOLIO.exitSignalDetail(holdingId || 0),
    enabled: enabled && !!holdingId,
    queryFn: () =>
      apiClient.get<ApiResponse<HoldingExitSignal>>(
        `portfolio/holdings/${holdingId}/exit-signal`,
      ),
    select: (response) => response.data,
  });

export const useRefreshHoldingExitSignal = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (holdingId: number) =>
      apiClient.post<ApiResponse<HoldingExitSignal>>(
        `portfolio/holdings/${holdingId}/exit-signal/refresh`,
      ),
    onSuccess: async (_response, holdingId) => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.PORTFOLIO.exitSignals,
        }),
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.PORTFOLIO.exitSignalDetail(holdingId),
        }),
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.PORTFOLIO.overview,
        }),
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.PORTFOLIO.holdings,
        }),
      ]);
    },
  });
};
