import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  StockAnalysisResearchTask,
  StockAnalysisResearchTaskGenerateResult,
  StockAnalysisResearchTaskList,
  StockAnalysisResearchTaskMutationResult,
} from "@/types/stock-analysis-research-task";

type CreateResearchTaskPayload = {
  title: string;
  summary?: string;
  task_type?: StockAnalysisResearchTask["task_type"];
  priority?: StockAnalysisResearchTask["priority"];
  source_kind?: StockAnalysisResearchTask["source_kind"];
  source_ref?: string | null;
  related_tickers_json?: string[];
  related_themes_json?: string[];
  related_context_ids_json?: number[];
  related_memory_id?: number | null;
  related_compression_id?: number | null;
  related_message_id?: string | null;
};

type TaskStatePayload = {
  note?: string;
};

const TASK_STALE_TIME_MS = 30 * 1000;
const TASK_GC_TIME_MS = 30 * 60 * 1000;

const invalidateResearchTaskQueries = (
  queryClient: ReturnType<typeof useQueryClient>,
  threadId: number,
) => {
  queryClient.invalidateQueries({
    queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.researchTasks(threadId),
  });
};

export const useGetStockAnalysisResearchTasks = (
  threadId?: number | null,
  enabled = true,
) =>
  useQuery({
    queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.researchTasks(threadId || 0),
    enabled: enabled && !!threadId,
    queryFn: () =>
      apiClient.get<ApiResponse<StockAnalysisResearchTaskList>>(
        `stock-analysis/threads/${threadId}/research-tasks`,
      ),
    select: (response) => response.data,
    placeholderData: keepPreviousData,
    staleTime: TASK_STALE_TIME_MS,
    gcTime: TASK_GC_TIME_MS,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });

export const useGenerateStockAnalysisResearchTasks = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ threadId }: { threadId: number }) =>
      apiClient.post<ApiResponse<StockAnalysisResearchTaskGenerateResult>>(
        `stock-analysis/threads/${threadId}/research-tasks/generate`,
        {},
      ),
    onSuccess: (_, variables) => {
      invalidateResearchTaskQueries(queryClient, variables.threadId);
    },
  });
};

export const useCreateStockAnalysisResearchTask = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      threadId,
      data,
    }: {
      threadId: number;
      data: CreateResearchTaskPayload;
    }) =>
      apiClient.post<ApiResponse<StockAnalysisResearchTaskMutationResult>>(
        `stock-analysis/threads/${threadId}/research-tasks`,
        data,
      ),
    onSuccess: (_, variables) => {
      invalidateResearchTaskQueries(queryClient, variables.threadId);
    },
  });
};

export const useCompleteStockAnalysisResearchTask = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      threadId,
      taskId,
      data,
    }: {
      threadId: number;
      taskId: number;
      data?: TaskStatePayload;
    }) =>
      apiClient.post<ApiResponse<StockAnalysisResearchTaskMutationResult>>(
        `stock-analysis/threads/${threadId}/research-tasks/${taskId}/complete`,
        data || {},
      ),
    onSuccess: (_, variables) => {
      invalidateResearchTaskQueries(queryClient, variables.threadId);
    },
  });
};

export const useReopenStockAnalysisResearchTask = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ threadId, taskId }: { threadId: number; taskId: number }) =>
      apiClient.post<ApiResponse<StockAnalysisResearchTaskMutationResult>>(
        `stock-analysis/threads/${threadId}/research-tasks/${taskId}/reopen`,
        {},
      ),
    onSuccess: (_, variables) => {
      invalidateResearchTaskQueries(queryClient, variables.threadId);
    },
  });
};

export const useDismissStockAnalysisResearchTask = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      threadId,
      taskId,
      data,
    }: {
      threadId: number;
      taskId: number;
      data?: TaskStatePayload;
    }) =>
      apiClient.post<ApiResponse<StockAnalysisResearchTaskMutationResult>>(
        `stock-analysis/threads/${threadId}/research-tasks/${taskId}/dismiss`,
        data || {},
      ),
    onSuccess: (_, variables) => {
      invalidateResearchTaskQueries(queryClient, variables.threadId);
    },
  });
};
