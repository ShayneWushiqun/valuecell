import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  DecisionAlertItem,
  DecisionAlertList,
  DecisionAlertReadAllResult,
  DecisionAlertSummary,
} from "@/types/decision-alert";

export const useGetDecisionAlertSummary = (enabled = true) =>
  useQuery({
    queryKey: API_QUERY_KEYS.DECISION_ALERT.summary,
    enabled,
    queryFn: () =>
      apiClient.get<ApiResponse<DecisionAlertSummary>>("decision-alerts/summary"),
    select: (response) => response.data,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  });

export const useGetDecisionAlerts = ({
  status = "all",
  alertType,
  limit = 50,
}: {
  status?: string;
  alertType?: string;
  limit?: number;
}) =>
  useQuery({
    queryKey: API_QUERY_KEYS.DECISION_ALERT.list(status, alertType || "all", limit),
    queryFn: () => {
      const searchParams = new URLSearchParams();
      searchParams.set("status", status);
      searchParams.set("limit", String(limit));
      if (alertType) {
        searchParams.set("alert_type", alertType);
      }
      return apiClient.get<ApiResponse<DecisionAlertList>>(
        `decision-alerts?${searchParams.toString()}`,
      );
    },
    select: (response) => response.data,
  });

const invalidateDecisionAlertQueries = async (queryClient: ReturnType<typeof useQueryClient>) => {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: API_QUERY_KEYS.DECISION_ALERT.summary }),
    queryClient.invalidateQueries({ queryKey: ["decision-alert", "list"] }),
  ]);
};

export const useRefreshDecisionAlerts = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<ApiResponse<DecisionAlertList>>("decision-alerts/refresh", {}),
    onSuccess: async () => {
      await invalidateDecisionAlertQueries(queryClient);
    },
  });
};

export const useMarkDecisionAlertRead = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (alertId: number) =>
      apiClient.put<ApiResponse<DecisionAlertItem>>(`decision-alerts/${alertId}/read`, {}),
    onSuccess: async () => {
      await invalidateDecisionAlertQueries(queryClient);
    },
  });
};

export const useMarkAllDecisionAlertsRead = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.put<ApiResponse<DecisionAlertReadAllResult>>("decision-alerts/read-all", {}),
    onSuccess: async () => {
      await invalidateDecisionAlertQueries(queryClient);
    },
  });
};

export const useDismissDecisionAlert = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (alertId: number) =>
      apiClient.put<ApiResponse<DecisionAlertItem>>(`decision-alerts/${alertId}/dismiss`, {}),
    onSuccess: async () => {
      await invalidateDecisionAlertQueries(queryClient);
    },
  });
};
