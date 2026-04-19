import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  TradingAgentsRunList,
  TradingAgentsRunRequest,
  TradingAgentsRunResult,
} from "@/types/tradingagents";

export const useCreateTradingAgentsRun = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TradingAgentsRunRequest) =>
      apiClient.post<ApiResponse<TradingAgentsRunResult>>("/tradingagents/runs", data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.TRADINGAGENTS.runList,
      });
    },
  });
};

export const useGetTradingAgentsRuns = (enabled = true) => {
  return useQuery({
    queryKey: API_QUERY_KEYS.TRADINGAGENTS.runList,
    enabled,
    queryFn: () =>
      apiClient.get<ApiResponse<TradingAgentsRunList>>("/tradingagents/runs"),
    select: (response) => response.data,
    staleTime: 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
    refetchInterval: (query) =>
      query.state.data?.data.running_count ? 3000 : false,
  });
};

export const useGetTradingAgentsRun = (runId?: string) => {
  return useQuery({
    queryKey: API_QUERY_KEYS.TRADINGAGENTS.runDetail([runId || ""]),
    queryFn: () =>
      apiClient.get<ApiResponse<TradingAgentsRunResult>>(`/tradingagents/runs/${runId}`),
    select: (response) => response.data,
    enabled: !!runId,
    refetchInterval: (query) => {
      const status = query.state.data?.data.status;
      if (status === "queued" || status === "running") {
        return 2000;
      }
      return false;
    },
  });
};
