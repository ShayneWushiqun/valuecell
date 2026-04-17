import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  AnalysisContextCard,
  AnalysisContextCardList,
  StockAnalysisContextImportResult,
} from "@/types/analysis-context-card";
import type {
  StockAnalysisThread,
  StockAnalysisThreadList,
  StockAnalysisWorkspaceOverview,
} from "@/types/stock-analysis-thread";

type CreateThreadPayload = {
  title: string;
  focus_type: string;
  ticker_refs_json?: string[];
  theme_refs_json?: string[];
};

type UpdateThreadPayload = {
  title?: string;
  focus_type?: string;
  ticker_refs_json?: string[];
  theme_refs_json?: string[];
};

type CreateContextPayload = {
  context_type: string;
  title: string;
  subtitle?: string | null;
  ticker_refs_json?: string[];
  theme_refs_json?: string[];
  summary: string;
  snapshot_payload_json?: Record<string, unknown>;
  source_module: string;
  source_ref?: string | null;
  staleness_hint?: string | null;
  is_pinned?: boolean;
  mode?: "append" | "replace";
};

type UpdateContextPayload = {
  title?: string;
  subtitle?: string | null;
  summary?: string;
  staleness_hint?: string | null;
  is_pinned?: boolean;
};

type ImportContextPayload = {
  source_module: string;
  source_ref: string;
  target_thread_id?: number;
  create_new_thread?: boolean;
  mode?: "append" | "replace";
};

export const useGetStockAnalysisThreads = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.threads,
    queryFn: () =>
      apiClient.get<ApiResponse<StockAnalysisThreadList>>("stock-analysis/threads"),
    select: (response) => response.data,
  });

export const useGetStockAnalysisWorkspaceOverview = (threadId?: number | null) =>
  useQuery({
    queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.overview(threadId || 0),
    queryFn: () =>
      apiClient.get<ApiResponse<StockAnalysisWorkspaceOverview>>(
        threadId
          ? `stock-analysis/workspace/overview?thread_id=${threadId}`
          : "stock-analysis/workspace/overview",
      ),
    select: (response) => response.data,
  });

export const useGetStockAnalysisContexts = (threadId?: number | null) =>
  useQuery({
    queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.contexts(threadId || 0),
    enabled: !!threadId,
    queryFn: () =>
      apiClient.get<ApiResponse<AnalysisContextCardList>>(
        `stock-analysis/threads/${threadId}/contexts`,
      ),
    select: (response) => response.data,
  });

export const useCreateStockAnalysisThread = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateThreadPayload) =>
      apiClient.post<ApiResponse<StockAnalysisThread>>("stock-analysis/threads", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.threads });
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.overviewBase,
      });
    },
  });
};

export const useUpdateStockAnalysisThread = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ threadId, data }: { threadId: number; data: UpdateThreadPayload }) =>
      apiClient.put<ApiResponse<StockAnalysisThread>>(
        `stock-analysis/threads/${threadId}`,
        data,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.threads });
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.overviewBase,
      });
    },
  });
};

export const useDeleteStockAnalysisThread = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (threadId: number) =>
      apiClient.delete<ApiResponse<StockAnalysisThread>>(
        `stock-analysis/threads/${threadId}`,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.threads });
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.overviewBase,
      });
    },
  });
};

export const useDuplicateStockAnalysisThread = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (threadId: number) =>
      apiClient.post<
        ApiResponse<{ thread: StockAnalysisThread; contexts: AnalysisContextCard[] }>
      >(`stock-analysis/threads/${threadId}/duplicate`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.threads });
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.overviewBase,
      });
    },
  });
};

export const useCreateStockAnalysisContext = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      threadId,
      data,
    }: {
      threadId: number;
      data: CreateContextPayload;
    }) =>
      apiClient.post<ApiResponse<AnalysisContextCard>>(
        `stock-analysis/threads/${threadId}/contexts`,
        data,
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.contexts(variables.threadId),
      });
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.overviewBase,
      });
    },
  });
};

export const useUpdateStockAnalysisContext = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      threadId,
      contextId,
      data,
    }: {
      threadId: number;
      contextId: number;
      data: UpdateContextPayload;
    }) =>
      apiClient.put<ApiResponse<AnalysisContextCard>>(
        `stock-analysis/threads/${threadId}/contexts/${contextId}`,
        data,
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.contexts(variables.threadId),
      });
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.overviewBase,
      });
    },
  });
};

export const useDeleteStockAnalysisContext = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      threadId,
      contextId,
    }: {
      threadId: number;
      contextId: number;
    }) =>
      apiClient.delete<ApiResponse<{ deleted: boolean }>>(
        `stock-analysis/threads/${threadId}/contexts/${contextId}`,
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.contexts(variables.threadId),
      });
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.overviewBase,
      });
    },
  });
};

export const useImportStockAnalysisContext = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ImportContextPayload) =>
      apiClient.post<ApiResponse<StockAnalysisContextImportResult>>(
        "stock-analysis/context-import",
        data,
      ),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.threads });
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.overviewBase,
      });
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK_ANALYSIS.contexts(response.data.thread.thread_id),
      });
    },
  });
};
