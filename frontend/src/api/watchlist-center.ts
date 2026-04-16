import { useQuery } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type { WatchlistCenterOverview } from "@/types/watchlist-center";

export const useGetWatchlistCenterOverview = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.WATCHLIST_CENTER.overview,
    queryFn: () =>
      apiClient.get<ApiResponse<WatchlistCenterOverview>>(
        "watchlist-center/overview",
      ),
    select: (response) => response.data,
  });
