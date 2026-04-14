import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  AShareDailyWorkbenchOverview,
  AShareDailyWorkbenchRefreshResult,
} from "@/types/ashare-daily-workbench";

export const useGetAShareDailyWorkbenchOverview = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.ASHARE_DAILY_WORKBENCH.overview,
    queryFn: () =>
      apiClient.get<ApiResponse<AShareDailyWorkbenchOverview>>(
        "ashare-workbench/overview",
      ),
    select: (response) => response.data,
  });

export const useRefreshAShareDailyWorkbench = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<ApiResponse<AShareDailyWorkbenchRefreshResult>>(
        "ashare-workbench/refresh",
        {},
      ),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.ASHARE_DAILY_WORKBENCH.overview,
        }),
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.DECISION_ALERT.summary,
        }),
        queryClient.invalidateQueries({
          queryKey: ["decision-alert", "list"],
        }),
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.PORTFOLIO.exitSignals,
        }),
      ]);
    },
  });
};
