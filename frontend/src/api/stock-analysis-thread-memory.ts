import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  StockAnalysisThreadMemory,
  StockAnalysisThreadMemoryActivateResult,
  StockAnalysisThreadMemoryCaptureResult,
  StockAnalysisThreadMemoryList,
} from "@/types/stock-analysis-thread-memory";

type CaptureMemoryPayload = {
  title?: string;
};

const MEMORY_STALE_TIME_MS = 60 * 1000;
const MEMORY_GC_TIME_MS = 30 * 60 * 1000;

export const useGetStockAnalysisThreadMemories = (
  threadId?: number | null,
  enabled = true,
) =>
  useQuery({
    queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.memories(threadId || 0),
    enabled: enabled && !!threadId,
    queryFn: () =>
      apiClient.get<ApiResponse<StockAnalysisThreadMemoryList>>(
        `stock-analysis/threads/${threadId}/memories`,
      ),
    select: (response) => response.data,
    placeholderData: keepPreviousData,
    staleTime: MEMORY_STALE_TIME_MS,
    gcTime: MEMORY_GC_TIME_MS,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });

export const useGetStockAnalysisThreadMemory = (
  threadId?: number | null,
  memoryId?: number | null,
) =>
  useQuery({
    queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.memoryDetail(threadId || 0, memoryId || 0),
    enabled: !!threadId && !!memoryId,
    queryFn: () =>
      apiClient.get<ApiResponse<StockAnalysisThreadMemory>>(
        `stock-analysis/threads/${threadId}/memories/${memoryId}`,
      ),
    select: (response) => response.data,
  });

export const useCaptureStockAnalysisThreadMemory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      threadId,
      data,
    }: {
      threadId: number;
      data?: CaptureMemoryPayload;
    }) =>
      apiClient.post<ApiResponse<StockAnalysisThreadMemoryCaptureResult>>(
        `stock-analysis/threads/${threadId}/memories/capture`,
        data || {},
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.memories(variables.threadId),
      });
    },
  });
};

export const useActivateStockAnalysisThreadMemory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      threadId,
      memoryId,
    }: {
      threadId: number;
      memoryId: number;
    }) =>
      apiClient.post<ApiResponse<StockAnalysisThreadMemoryActivateResult>>(
        `stock-analysis/threads/${threadId}/memories/${memoryId}/activate`,
        {},
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.memories(variables.threadId),
      });
    },
  });
};

export const useRefreshStockAnalysisThreadMemory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      threadId,
      memoryId,
      data,
    }: {
      threadId: number;
      memoryId: number;
      data?: CaptureMemoryPayload;
    }) =>
      apiClient.post<ApiResponse<StockAnalysisThreadMemoryCaptureResult>>(
        `stock-analysis/threads/${threadId}/memories/${memoryId}/refresh`,
        data || {},
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.memories(variables.threadId),
      });
    },
  });
};
