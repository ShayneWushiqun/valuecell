import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  DecisionRecord,
  DecisionRecordCapture,
  DecisionRecordList,
} from "@/types/decision-record";

export const useGetDecisionRecords = ({
  limit = 20,
  action,
}: {
  limit?: number;
  action?: string;
}) =>
  useQuery({
    queryKey: API_QUERY_KEYS.DECISION_RECORD.list(limit, action || "all"),
    queryFn: () =>
      apiClient.get<ApiResponse<DecisionRecordList>>(
        `decision-records?limit=${limit}${action ? `&action=${encodeURIComponent(action)}` : ""}`,
      ),
    select: (response) => response.data,
  });

export const useGetDecisionRecordDetail = (
  recordId: number | null,
  enabled = true,
) =>
  useQuery({
    queryKey: API_QUERY_KEYS.DECISION_RECORD.detail(recordId || 0),
    enabled: enabled && !!recordId,
    queryFn: () =>
      apiClient.get<ApiResponse<DecisionRecord>>(`decision-records/${recordId}`),
    select: (response) => response.data,
  });

const invalidateDecisionRecordQueries = async (queryClient: ReturnType<typeof useQueryClient>) => {
  await Promise.all([
    queryClient.invalidateQueries({
      queryKey: API_QUERY_KEYS.DECISION_RECORD.base,
    }),
    queryClient.invalidateQueries({
      queryKey: API_QUERY_KEYS.ASHARE_DAILY_SNAPSHOT.list(14, true),
    }),
  ]);
};

export const useCaptureDecisionRecords = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<ApiResponse<DecisionRecordCapture>>("decision-records/capture"),
    onSuccess: async () => invalidateDecisionRecordQueries(queryClient),
  });
};

export const useRefreshDecisionRecords = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<ApiResponse<DecisionRecordCapture>>("decision-records/refresh"),
    onSuccess: async () => invalidateDecisionRecordQueries(queryClient),
  });
};
