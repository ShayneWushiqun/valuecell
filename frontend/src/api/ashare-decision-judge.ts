import { useMutation } from "@tanstack/react-query";
import { type ApiResponse, apiClient } from "@/lib/api-client";
import type {
  AShareDecisionJudgePayload,
  AShareDecisionJudgeResult,
} from "@/types/ashare-decision-judge";

export const useGenerateAShareDecisionJudge = () =>
  useMutation({
    mutationFn: (payload: AShareDecisionJudgePayload) =>
      apiClient.post<ApiResponse<AShareDecisionJudgeResult>>(
        "ashare-decision/judge",
        payload,
      ),
  });
