import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  ExitRiskCenterOverview,
  ExitRiskCenterRefresh,
} from "@/types/exit-risk-center";

export const useGetExitRiskCenterOverview = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.EXIT_RISK_CENTER.overview,
    queryFn: () =>
      apiClient.get<ApiResponse<ExitRiskCenterOverview>>(
        "exit-risk-center/overview",
      ),
    select: (response) => response.data,
  });

export const useRefreshExitRiskCenter = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<ApiResponse<ExitRiskCenterRefresh>>(
        "exit-risk-center/refresh",
      ),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.EXIT_RISK_CENTER.overview,
        }),
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.HOLDING_LIFECYCLE.overview,
        }),
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.PORTFOLIO.exitSignals,
        }),
      ]);
    },
  });
};
