import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  StrategyPreferenceProfile,
  StrategyPreferenceTemplateList,
  UpdateStrategyPreferencePayload,
} from "@/types/strategy-preference";

export const useGetStrategyPreferenceTemplates = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.STRATEGY_PREFERENCE.templates,
    queryFn: () =>
      apiClient.get<ApiResponse<StrategyPreferenceTemplateList>>(
        "strategy-preferences/templates",
      ),
    select: (response) => response.data,
  });

export const useGetStrategyPreferenceProfile = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.STRATEGY_PREFERENCE.profile,
    queryFn: () =>
      apiClient.get<ApiResponse<StrategyPreferenceProfile>>(
        "strategy-preferences/profile",
      ),
    select: (response) => response.data,
  });

export const useUpdateStrategyPreferenceProfile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateStrategyPreferencePayload) =>
      apiClient.put<ApiResponse<StrategyPreferenceProfile>>(
        "strategy-preferences/profile",
        payload,
      ),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.STRATEGY_PREFERENCE.profile,
        }),
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.OPPORTUNITY_POOL.candidates,
        }),
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.ENTRY_TIMING.signals,
        }),
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.DECISION_ALERT.summary,
        }),
      ]);
    },
  });
};
