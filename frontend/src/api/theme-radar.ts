import { useQuery } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type { ThemeRadarOverview } from "@/types/theme-radar";

export const useGetThemeRadarOverview = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.THEME_RADAR.overview,
    queryFn: () =>
      apiClient.get<ApiResponse<ThemeRadarOverview>>("theme-radar/overview"),
    select: (response) => response.data,
  });
