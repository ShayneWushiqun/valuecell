import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_QUERY_KEYS } from "@/constants/api";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  AShareDailySnapshotDetail,
  AShareDailySnapshotList,
  AShareDailySnapshotRefreshResult,
} from "@/types/ashare-daily-snapshot";

export const useGetAShareDailySnapshots = ({
  limit = 20,
  includeToday = true,
}: {
  limit?: number;
  includeToday?: boolean;
}) =>
  useQuery({
    queryKey: API_QUERY_KEYS.ASHARE_DAILY_SNAPSHOT.list(limit, includeToday),
    queryFn: () =>
      apiClient.get<ApiResponse<AShareDailySnapshotList>>(
        `ashare-workbench/snapshots?limit=${limit}&include_today=${includeToday}`,
      ),
    select: (response) => response.data,
  });

export const useGetAShareDailySnapshotDetail = (
  snapshotDate: string | null,
  enabled = true,
) =>
  useQuery({
    queryKey: API_QUERY_KEYS.ASHARE_DAILY_SNAPSHOT.detail(snapshotDate || ""),
    enabled: enabled && !!snapshotDate,
    queryFn: () =>
      apiClient.get<ApiResponse<AShareDailySnapshotDetail>>(
        `ashare-workbench/snapshots/${snapshotDate}`,
      ),
    select: (response) => response.data,
  });

export const useRefreshAShareDailySnapshot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<ApiResponse<AShareDailySnapshotRefreshResult>>(
        "ashare-workbench/snapshots/refresh",
        {},
      ),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["ashare-daily-snapshot"],
        }),
        queryClient.invalidateQueries({
          queryKey: API_QUERY_KEYS.ASHARE_DAILY_WORKBENCH.overview,
        }),
      ]);
    },
  });
};
