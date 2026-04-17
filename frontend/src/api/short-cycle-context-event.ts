import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type { ShortCycleContextEventList } from "@/types/short-cycle-context-event";

export const useGetShortCycleContextEvents = ({
  ticker,
  limit = 200,
}: {
  ticker?: string;
  limit?: number;
}) =>
  useQuery({
    queryKey: API_QUERY_KEYS.SHORT_CYCLE_CONTEXT_EVENT.list(ticker || "all", limit),
    queryFn: () =>
      apiClient.get<ApiResponse<ShortCycleContextEventList>>(
        `short-cycle-context-events?limit=${limit}${ticker ? `&ticker=${encodeURIComponent(ticker)}` : ""}`,
      ),
    select: (response) => response.data,
  });

export const useRefreshShortCycleContextEvents = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ticker?: string) =>
      apiClient.post<ApiResponse<ShortCycleContextEventList>>(
        "short-cycle-context-events/refresh",
        ticker ? { ticker } : {},
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: API_QUERY_KEYS.SHORT_CYCLE_CONTEXT_EVENT.base,
      });
    },
  });
};
