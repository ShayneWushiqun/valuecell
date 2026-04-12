import { useQuery } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type { EntryTimingSignals } from "@/types/entry-timing";

export const useGetEntryTimingSignals = () =>
  useQuery({
    queryKey: API_QUERY_KEYS.ENTRY_TIMING.signals,
    queryFn: () =>
      apiClient.get<ApiResponse<EntryTimingSignals>>("entry-timing/signals"),
    select: (response) => response.data,
  });
