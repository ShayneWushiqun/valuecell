import { useQuery } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type { HomepageContext } from "@/types/homepage-context";

export const useGetHomepageContext = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.HOMEPAGE.context,
    queryFn: () =>
      apiClient.get<ApiResponse<HomepageContext>>("homepage/context"),
    select: (response) => response.data,
  });
