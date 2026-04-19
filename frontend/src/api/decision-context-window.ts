import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type { DecisionContextWindowList } from "@/types/decision-context-window";

export const useGetDecisionContextWindows = ({
  ticker,
  windowSize,
  limit = 100,
  enabled = true,
}: {
  ticker?: string;
  windowSize?: number;
  limit?: number;
  enabled?: boolean;
}) =>
  useQuery({
    queryKey: API_QUERY_KEYS.DECISION_CONTEXT_WINDOW.list(
      ticker || "all",
      windowSize || 0,
      limit,
    ),
    enabled,
    queryFn: () =>
      apiClient.get<ApiResponse<DecisionContextWindowList>>(
        `decision-context-windows?limit=${limit}${ticker ? `&ticker=${encodeURIComponent(ticker)}` : ""}${windowSize ? `&window_size=${windowSize}` : ""}`,
      ),
    select: (response) => response.data,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });

export const useRefreshDecisionContextWindows = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ticker?: string) =>
      apiClient.post<ApiResponse<DecisionContextWindowList>>(
        "decision-context-windows/refresh",
        ticker ? { ticker } : {},
      ),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.DECISION_CONTEXT_WINDOW.base,
        }),
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.SHORT_CYCLE_CONTEXT_EVENT.base,
        }),
      ]);
    },
  });
};
