import { StockAnalysisResearchTaskItem } from "@/app/home/components/stock-analysis-research-task-item";
import type { StockAnalysisResearchTask } from "@/types/stock-analysis-research-task";

type StockAnalysisResearchTaskListProps = {
  tasks: StockAnalysisResearchTask[];
  emptyText: string;
  actionPending?: boolean;
  onResearch: (task: StockAnalysisResearchTask) => void;
  onComplete: (task: StockAnalysisResearchTask) => void;
  onReopen: (task: StockAnalysisResearchTask) => void;
  onDismiss: (task: StockAnalysisResearchTask) => void;
};

export function StockAnalysisResearchTaskList({
  tasks,
  emptyText,
  actionPending = false,
  onResearch,
  onComplete,
  onReopen,
  onDismiss,
}: StockAnalysisResearchTaskListProps) {
  if (!tasks.length) {
    return (
      <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
        {emptyText}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <StockAnalysisResearchTaskItem
          key={task.task_id}
          task={task}
          actionPending={actionPending}
          onResearch={onResearch}
          onComplete={onComplete}
          onReopen={onReopen}
          onDismiss={onDismiss}
        />
      ))}
    </div>
  );
}
