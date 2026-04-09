import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  CreateHoldingRequest,
  DailyBriefing,
  HoldingDiagnosis,
  HoldingList,
  PortfolioOverview,
  UserHolding,
} from "@/types/portfolio";

export const useGetPortfolioOverview = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.PORTFOLIO.overview,
    queryFn: () => apiClient.get<ApiResponse<PortfolioOverview>>("portfolio/overview"),
    select: (response) => response.data,
  });

export const useGetHoldings = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.PORTFOLIO.holdings,
    queryFn: () => apiClient.get<ApiResponse<HoldingList>>("portfolio/holdings"),
    select: (response) => response.data,
  });

export const useRefreshDailyBriefing = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<ApiResponse<DailyBriefing>>("portfolio/briefings/daily"),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.PORTFOLIO.overview,
      });
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.PORTFOLIO.holdings,
      });
    },
  });
};

export const useCreateHolding = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateHoldingRequest) =>
      apiClient.post<ApiResponse<UserHolding>>("portfolio/holdings", payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.PORTFOLIO.overview,
      });
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.PORTFOLIO.holdings,
      });
    },
  });
};

export const useUpdateHolding = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      holdingId,
      payload,
    }: {
      holdingId: number;
      payload: CreateHoldingRequest;
    }) =>
      apiClient.put<ApiResponse<UserHolding>>(
        `portfolio/holdings/${holdingId}`,
        payload,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.PORTFOLIO.overview,
      });
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.PORTFOLIO.holdings,
      });
    },
  });
};

export const useDeleteHolding = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (holdingId: number) =>
      apiClient.delete<ApiResponse<{ deleted: boolean }>>(
        `portfolio/holdings/${holdingId}`,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.PORTFOLIO.overview,
      });
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.PORTFOLIO.holdings,
      });
    },
  });
};

export const useRefreshHoldingDiagnosis = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (holdingId: number) =>
      apiClient.post<ApiResponse<HoldingDiagnosis>>(
        `portfolio/holdings/${holdingId}/diagnosis`,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.PORTFOLIO.overview,
      });
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.PORTFOLIO.holdings,
      });
    },
  });
};
