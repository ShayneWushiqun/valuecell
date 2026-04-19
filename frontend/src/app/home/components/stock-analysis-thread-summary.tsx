import { ChevronDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

type StockAnalysisThreadSummaryProps = {
  threadHealthStatus?: string | null;
  threadHealthScore?: number | null;
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
  latestFeedbackAlignmentStatus?: string | null;
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
  threadHealthStatus,
  threadHealthScore,
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
  latestFeedbackAlignmentStatus,
  recentFeedbackMethodBias,
  recentResearchQualityTrend,
  lastRefreshAt,
  lastRefreshSummary,
}: StockAnalysisThreadSummaryProps) {
  const coreMetrics = [
    {
      label: "对比对象",
      value: `${compareTargetCount}`,
      hint: compareTargetCount ? "已显式管理" : "尚未添加",
    },
    {
      label: "上下文状态",
      value: staleCount ? `${staleCount} 张较旧` : "状态稳定",
      hint: refreshRecommendedCount ? `${refreshRecommendedCount} 张建议刷新` : "暂无建议刷新",
    },
    {
      label: "研究任务",
      value: `${openResearchTaskCount} 项待处理`,
      hint: highPriorityResearchTaskCount
        ? `${highPriorityResearchTaskCount} 项高优先级`
        : "暂无高优先级任务",
    },
    {
      label: "冲突等级",
      value: currentEvidenceConflictLevel || "未见明显冲突",
      hint: currentPlanningProfile ? `当前策略：${currentPlanningProfile}` : "等待下一轮研究更新",
    },
    {
      label: "研究记忆",
      value: activeMemoryAvailable ? "可继续参考" : "尚未沉淀",
      hint: activeCompressionAvailable ? "对话摘要可用" : "暂无对话摘要",
    },
    {
      label: "最近刷新",
      value: formatTime(lastRefreshAt),
      hint: lastRefreshSummary || "还没有上下文刷新记录",
    },
  ];

  return (
    <div className="rounded-xl border p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary">线程摘要</Badge>
        {threadHealthStatus ? (
          <Badge variant="outline">
            健康状态 {threadHealthStatus}
            {typeof threadHealthScore === "number" ? ` · ${threadHealthScore}` : ""}
          </Badge>
        ) : null}
        {latestFeedbackAlignmentStatus ? (
          <Badge variant="outline">近期反馈：{latestFeedbackAlignmentStatus}</Badge>
        ) : null}
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {coreMetrics.map((metric) => (
          <div key={metric.label} className="rounded-lg border bg-muted/20 p-3">
            <p className="text-muted-foreground text-xs">{metric.label}</p>
            <p className="mt-1 font-medium text-sm">{metric.value}</p>
            <p className="mt-1 line-clamp-2 text-muted-foreground text-xs">{metric.hint}</p>
          </div>
        ))}
      </div>

      <details className="mt-4 rounded-lg border border-dashed p-3">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 font-medium text-sm">
          查看线程详情
          <Button variant="ghost" size="icon" className="pointer-events-none size-7">
            <ChevronDown className="size-4" />
          </Button>
        </summary>
        <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
          <p>相关任务：{relatedTaskCount}</p>
          <p>长期证据：{savedEvidenceCount}</p>
          <p>最近任务生成：{formatTime(lastResearchTaskGenerateAt)}</p>
          <p>
            反馈数量：{recentFeedbackCount}
            {lastFeedbackOutcomeStatus ? ` · 结果 ${lastFeedbackOutcomeStatus}` : ""}
          </p>
          <p>
            对话整理：{compressionRecommended ? "建议重新整理" : "当前无需整理"}
            {activeCompressionStale ? " · 当前摘要偏旧" : ""}
          </p>
          <p>
            最近执行：{lastExecutionTriggeredRefresh ? "已做刷新" : "未做刷新"} /{" "}
            {lastExecutionTriggeredTooling ? "已补数据" : "未补数据"} /{" "}
            {lastExecutionTriggeredValidation ? "已校验" : "未校验"}
          </p>
          <p>{actionableTaskGapSummary || "当前没有明显的待补研究缺口。"}</p>
          <p>{lastValidationSummary || "当前还没有最近一轮结论校验摘要。"}</p>
          <p>{lastFeedbackSummary || "当前还没有研究反馈摘要。"}</p>
          <p>{compressionReason || "当前线程如果继续增长，可手动整理对话。"}</p>
          {lastFeedbackProcessQualityStatus ? (
            <p>过程质量：{lastFeedbackProcessQualityStatus}</p>
          ) : null}
          {recentFeedbackMethodBias ? <p>近期方式偏好：{recentFeedbackMethodBias}</p> : null}
          {recentResearchQualityTrend ? <p>近期研究趋势：{recentResearchQualityTrend}</p> : null}
          <p>{hasTrackingFollowupTasks ? "存在继续跟踪建议。" : "暂无继续跟踪建议。"}</p>
          <p>未压缩消息：{uncompressedMessageCount}</p>
          <p>{hasActionableTaskGap ? "存在需要立即行动的任务缺口。" : "当前任务缺口可控。"}</p>
        </div>
      </details>
    </div>
  );
}
