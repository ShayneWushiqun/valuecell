import { Badge } from "@/components/ui/badge";

type StockAnalysisThreadSummaryProps = {
  compareTargetCount: number;
  staleCount: number;
  refreshRecommendedCount: number;
  savedEvidenceCount: number;
  activeMemoryAvailable: boolean;
  activeCompressionAvailable: boolean;
  compressionRecommended: boolean;
  activeCompressionStale: boolean;
  uncompressedMessageCount: number;
  compressionReason?: string | null;
  openResearchTaskCount: number;
  highPriorityResearchTaskCount: number;
  relatedTaskCount: number;
  lastResearchTaskGenerateAt?: string | null;
  hasActionableTaskGap: boolean;
  actionableTaskGapSummary?: string | null;
  lastExecutionTriggeredRefresh: boolean;
  lastExecutionTriggeredTooling: boolean;
  lastExecutionTriggeredValidation: boolean;
  lastValidationSummary?: string | null;
  recentFeedbackCount: number;
  lastFeedbackOutcomeStatus?: string | null;
  lastFeedbackProcessQualityStatus?: string | null;
  hasTrackingFollowupTasks: boolean;
  lastFeedbackSummary?: string | null;
  currentPlanningProfile?: string | null;
  currentEvidenceConflictLevel?: string | null;
  recentFeedbackMethodBias?: string | null;
  recentResearchQualityTrend?: string | null;
  lastRefreshAt?: string | null;
  lastRefreshSummary?: string | null;
};

const formatTime = (value?: string | null) => {
  if (!value) return "暂无";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN");
};

export function StockAnalysisThreadSummary({
  compareTargetCount,
  staleCount,
  refreshRecommendedCount,
  savedEvidenceCount,
  activeMemoryAvailable,
  activeCompressionAvailable,
  compressionRecommended,
  activeCompressionStale,
  uncompressedMessageCount,
  compressionReason,
  openResearchTaskCount,
  highPriorityResearchTaskCount,
  relatedTaskCount,
  lastResearchTaskGenerateAt,
  hasActionableTaskGap,
  actionableTaskGapSummary,
  lastExecutionTriggeredRefresh,
  lastExecutionTriggeredTooling,
  lastExecutionTriggeredValidation,
  lastValidationSummary,
  recentFeedbackCount,
  lastFeedbackOutcomeStatus,
  lastFeedbackProcessQualityStatus,
  hasTrackingFollowupTasks,
  lastFeedbackSummary,
  currentPlanningProfile,
  currentEvidenceConflictLevel,
  recentFeedbackMethodBias,
  recentResearchQualityTrend,
  lastRefreshAt,
  lastRefreshSummary,
}: StockAnalysisThreadSummaryProps) {
  return (
    <div className="rounded-xl border p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary">研究流摘要</Badge>
        <Badge variant="outline">对比对象 {compareTargetCount}</Badge>
        <Badge variant="outline">较旧上下文 {staleCount}</Badge>
        <Badge variant="outline">建议刷新 {refreshRecommendedCount}</Badge>
        <Badge variant="outline">长期证据 {savedEvidenceCount}</Badge>
        <Badge variant="outline">
          研究记忆 {activeMemoryAvailable ? "已启用" : "未启用"}
        </Badge>
        <Badge variant="outline">
          对话压缩 {activeCompressionAvailable ? "已启用" : "未启用"}
        </Badge>
        <Badge variant="outline">
          未压缩消息 {uncompressedMessageCount}
        </Badge>
        <Badge variant="outline">Open tasks {openResearchTaskCount}</Badge>
        <Badge variant="outline">High tasks {highPriorityResearchTaskCount}</Badge>
        <Badge variant="outline">当前相关 {relatedTaskCount}</Badge>
        <Badge variant={compressionRecommended ? "secondary" : "outline"}>
          {compressionRecommended ? "建议压缩" : "当前无需压缩"}
        </Badge>
        <Badge variant={activeCompressionStale ? "secondary" : "outline"}>
          {activeCompressionStale ? "压缩偏旧" : "压缩可用"}
        </Badge>
        <Badge variant={hasActionableTaskGap ? "secondary" : "outline"}>
          {hasActionableTaskGap ? "存在任务 gap" : "当前任务 gap 可控"}
        </Badge>
        <Badge variant={lastExecutionTriggeredRefresh ? "secondary" : "outline"}>
          {lastExecutionTriggeredRefresh ? "最近计划触发 refresh" : "最近计划未触发 refresh"}
        </Badge>
        <Badge variant={lastExecutionTriggeredTooling ? "secondary" : "outline"}>
          {lastExecutionTriggeredTooling ? "最近计划触发 tooling" : "最近计划未触发 tooling"}
        </Badge>
        <Badge variant={lastExecutionTriggeredValidation ? "secondary" : "outline"}>
          {lastExecutionTriggeredValidation ? "最近计划触发 validation" : "最近计划未触发 validation"}
        </Badge>
        <Badge variant="outline">Research feedback {recentFeedbackCount}</Badge>
        <Badge variant={hasTrackingFollowupTasks ? "secondary" : "outline"}>
          {hasTrackingFollowupTasks ? "存在继续跟踪建议" : "暂无继续跟踪建议"}
        </Badge>
        {lastFeedbackOutcomeStatus ? (
          <Badge variant="outline">最近 feedback: {lastFeedbackOutcomeStatus}</Badge>
        ) : null}
        {lastFeedbackProcessQualityStatus ? (
          <Badge variant="outline">过程偏 {lastFeedbackProcessQualityStatus}</Badge>
        ) : null}
        {currentPlanningProfile ? (
          <Badge variant="outline">planning {currentPlanningProfile}</Badge>
        ) : null}
        {currentEvidenceConflictLevel ? (
          <Badge variant="outline">conflict {currentEvidenceConflictLevel}</Badge>
        ) : null}
        {recentFeedbackMethodBias ? (
          <Badge variant="outline">反馈偏向 {recentFeedbackMethodBias}</Badge>
        ) : null}
        {recentResearchQualityTrend ? (
          <Badge variant="outline">近期趋势 {recentResearchQualityTrend}</Badge>
        ) : null}
      </div>
      <div className="mt-3 space-y-2 text-sm">
        <p className="text-muted-foreground">
          最近一次批量刷新：{formatTime(lastRefreshAt)}
        </p>
        <p>{lastRefreshSummary || "当前还没有批量刷新记录。"}</p>
        <p className="text-muted-foreground">
          最近一次任务生成：{formatTime(lastResearchTaskGenerateAt)}
        </p>
        <p>{actionableTaskGapSummary || "当前还没有需要立即处理的 research task gap。"}</p>
        <p>{lastValidationSummary || "当前还没有最近一轮 thesis validation 摘要。"}</p>
        <p>{lastFeedbackSummary || "当前还没有研究反馈摘要。"}</p>
        <p className="text-muted-foreground">
          {compressionReason || "当前线程如果继续增长，可手动整理对话。"}
        </p>
      </div>
    </div>
  );
}
