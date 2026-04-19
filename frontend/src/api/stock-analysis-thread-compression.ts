import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  StockAnalysisThreadCompression,
  StockAnalysisThreadCompressionActivateResult,
  StockAnalysisThreadCompressionCaptureResult,
  StockAnalysisThreadCompressionList,
} from "@/types/stock-analysis-thread-compression";

type CaptureCompressionPayload = {
  title?: string;
};

const COMPRESSION_STALE_TIME_MS = 60 * 1000;
const COMPRESSION_GC_TIME_MS = 30 * 60 * 1000;

export const useGetStockAnalysisThreadCompressions = (
  threadId?: number | null,
  enabled = true,
) =>
  useQuery({
    queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.compressions(threadId || 0),
    enabled: enabled && !!threadId,
    queryFn: () =>
      apiClient.get<ApiResponse<StockAnalysisThreadCompressionList>>(
        `stock-analysis/threads/${threadId}/compressions`,
      ),
    select: (response) => response.data,
    placeholderData: keepPreviousData,
    staleTime: COMPRESSION_STALE_TIME_MS,
    gcTime: COMPRESSION_GC_TIME_MS,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  });

export const useGetStockAnalysisThreadCompression = (
  threadId?: number | null,
  compressionId?: number | null,
) =>
  useQuery({
    queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.compressionDetail(
      threadId || 0,
      compressionId || 0,
    ),
    enabled: !!threadId && !!compressionId,
    queryFn: () =>
      apiClient.get<ApiResponse<StockAnalysisThreadCompression>>(
        `stock-analysis/threads/${threadId}/compressions/${compressionId}`,
      ),
    select: (response) => response.data,
  });

export const useCaptureStockAnalysisThreadCompression = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      threadId,
      data,
    }: {
      threadId: number;
      data?: CaptureCompressionPayload;
    }) =>
      apiClient.post<ApiResponse<StockAnalysisThreadCompressionCaptureResult>>(
        `stock-analysis/threads/${threadId}/compressions/capture`,
        data || {},
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.compressions(variables.threadId),
      });
    },
  });
};

export const useActivateStockAnalysisThreadCompression = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      threadId,
      compressionId,
    }: {
      threadId: number;
      compressionId: number;
    }) =>
      apiClient.post<ApiResponse<StockAnalysisThreadCompressionActivateResult>>(
        `stock-analysis/threads/${threadId}/compressions/${compressionId}/activate`,
        {},
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.compressions(variables.threadId),
      });
    },
  });
};

export const useRefreshStockAnalysisThreadCompression = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      threadId,
      compressionId,
      data,
    }: {
      threadId: number;
      compressionId: number;
      data?: CaptureCompressionPayload;
    }) =>
      apiClient.post<ApiResponse<StockAnalysisThreadCompressionCaptureResult>>(
        `stock-analysis/threads/${threadId}/compressions/${compressionId}/refresh`,
        data || {},
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.compressions(variables.threadId),
      });
    },
  });
};
