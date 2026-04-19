import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  StockAnalysisResearchFeedback,
  StockAnalysisResearchFeedbackList,
  StockAnalysisResearchFeedbackMutationResult,
} from "@/types/stock-analysis-research-feedback";

type CaptureResearchFeedbackPayload = {
  anchor_message_id?: string;
  related_task_ids?: number[];
  related_tickers?: string[];
  title?: string;
  note?: string;
};

const FEEDBACK_STALE_TIME_MS = 60 * 1000;
const FEEDBACK_GC_TIME_MS = 30 * 60 * 1000;

export const useGetStockAnalysisResearchFeedback = (
  threadId?: number | null,
  enabled = true,
) =>
  useQuery({
    queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.researchFeedback(threadId || 0),
    enabled: enabled && !!threadId,
    queryFn: () =>
      apiClient.get<ApiResponse<StockAnalysisResearchFeedbackList>>(
        `stock-analysis/threads/${threadId}/research-feedback`,
      ),
    select: (response) => response.data,
    placeholderData: keepPreviousData,
    staleTime: FEEDBACK_STALE_TIME_MS,
    gcTime: FEEDBACK_GC_TIME_MS,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });

export const useGetStockAnalysisResearchFeedbackDetail = (
  threadId?: number | null,
  feedbackId?: number | null,
) =>
  useQuery({
    queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.researchFeedbackDetail(
      threadId || 0,
      feedbackId || 0,
    ),
    enabled: !!threadId && !!feedbackId,
    queryFn: () =>
      apiClient.get<ApiResponse<StockAnalysisResearchFeedback>>(
        `stock-analysis/threads/${threadId}/research-feedback/${feedbackId}`,
      ),
    select: (response) => response.data,
  });

export const useCaptureStockAnalysisResearchFeedback = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      threadId,
      data,
    }: {
      threadId: number;
      data?: CaptureResearchFeedbackPayload;
    }) =>
      apiClient.post<ApiResponse<StockAnalysisResearchFeedbackMutationResult>>(
        `stock-analysis/threads/${threadId}/research-feedback/capture`,
        data || {},
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.researchFeedback(variables.threadId),
      });
    },
  });
};

export const useRefreshStockAnalysisResearchFeedback = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      threadId,
      feedbackId,
      data,
    }: {
      threadId: number;
      feedbackId: number;
      data?: CaptureResearchFeedbackPayload;
    }) =>
      apiClient.post<ApiResponse<StockAnalysisResearchFeedbackMutationResult>>(
        `stock-analysis/threads/${threadId}/research-feedback/${feedbackId}/refresh`,
        data || {},
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.researchFeedback(variables.threadId),
      });
    },
  });
};
