import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { API_QUERY_KEYS, VALUECELL_BACKEND_URL } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import { useLanguage } from "@/store/settings-store";
import { useSystemStore } from "@/store/system-store";
import type {
  Stock,
  StockDetail,
  StockHistory,
  StockInterval,
  StockPrice,
  Watchlist,
} from "@/types/stock";

export const useGetWatchlist = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.STOCK.watchlist,
    queryFn: () => apiClient.get<ApiResponse<Watchlist[]>>("watchlist/"),
    select: (data) => data.data,
    staleTime: 3 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  });

export const useGetStocksList = (params: { query: string }) => {
  const language = useLanguage();

  return useQuery({
    queryKey: API_QUERY_KEYS.STOCK.stockSearch([params.query, language]),
    queryFn: ({ signal }) =>
      apiClient.get<ApiResponse<{ results: Stock[] }>>(
        `watchlist/asset/search?q=${params.query}&language=${language}`,
        { signal },
      ),
    select: (data) => data.data.results,
    enabled: params.query.trim().length >= 2,
    placeholderData: keepPreviousData,
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
    retry: false,
  });
};

export const useAddStockToWatchlist = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ticker: Pick<Stock, "ticker">) =>
      apiClient.post<ApiResponse<null>>("watchlist/asset", ticker),
    onSuccess: () => {
      // invalidate watchlist query cache to trigger re-fetch
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK.watchlist,
      });
    },
  });
};

export const useRemoveStockFromWatchlist = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ticker: string) =>
      apiClient.delete<ApiResponse<null>>(`watchlist/asset/${ticker}`),
    onSuccess: () => {
      // invalidate watchlist query cache to trigger re-fetch
      queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.STOCK.watchlist,
      });
    },
  });
};

export const useGetStockPrice = (params: { ticker: string }) =>
  useQuery({
    queryKey: API_QUERY_KEYS.STOCK.stockPrice(Object.values(params)),
    queryFn: () =>
      apiClient.get<ApiResponse<StockPrice>>(
        `${useSystemStore.getState().access_token ? "" : ""}/watchlist/asset/${params.ticker}/price`,
        {
          requiresAuth: !!useSystemStore.getState().access_token,
        },
      ),
    select: (data) => data.data,
    enabled: !!params.ticker,
    staleTime: 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  });

export const useGetStockHistory = (params: {
  ticker: string;
  interval: StockInterval;
  start_date: string;
  end_date: string;
}) =>
  useQuery({
    queryKey: API_QUERY_KEYS.STOCK.stockHistory(Object.values(params)),
    queryFn: () =>
      apiClient.get<ApiResponse<StockHistory[]>>(
        `${VALUECELL_BACKEND_URL}/watchlist/asset/${params.ticker}/price/historical?interval=${params.interval}&start_date=${params.start_date}&end_date=${params.end_date}`,
        {
          requiresAuth: true,
        },
      ),
    select: (data) => data.data,
    enabled: !!params.ticker,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  });

export const useGetStockDetail = (params: { ticker: string }) =>
  useQuery({
    queryKey: API_QUERY_KEYS.STOCK.stockDetail(Object.values(params)),
    queryFn: () =>
      apiClient.get<ApiResponse<StockDetail>>(
        `${useSystemStore.getState().access_token ? "" : ""}/watchlist/asset/${params.ticker}`,
        {
          requiresAuth: !!useSystemStore.getState().access_token,
        },
      ),
    select: (data) => data.data,
    enabled: !!params.ticker,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  });
