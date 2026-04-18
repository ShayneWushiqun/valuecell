import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type StockAnalysisForkDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  onTitleChange: (value: string) => void;
  selectedContextCount: number;
  includeCompareTargets: boolean;
  onIncludeCompareTargetsChange: (value: boolean) => void;
  pinImportedContexts: boolean;
  onPinImportedContextsChange: (value: boolean) => void;
  focusTypeOverride: string;
  onFocusTypeOverrideChange: (value: string) => void;
  onSubmit: () => void;
  isSubmitting?: boolean;
};

const FOCUS_OPTIONS = [
  { value: "inherit", label: "沿用当前 focus" },
  { value: "comparison", label: "comparison" },
  { value: "ticker", label: "ticker" },
  { value: "theme", label: "theme" },
  { value: "mixed", label: "mixed" },
] as const;

export function StockAnalysisForkDialog({
  open,
  onOpenChange,
  title,
  onTitleChange,
  selectedContextCount,
  includeCompareTargets,
  onIncludeCompareTargetsChange,
  pinImportedContexts,
  onPinImportedContextsChange,
  focusTypeOverride,
  onFocusTypeOverrideChange,
  onSubmit,
  isSubmitting = false,
}: StockAnalysisForkDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>分叉研究线程</DialogTitle>
          <DialogDescription>
            新线程会继承所选上下文和可选 compare targets，但不会复制旧聊天历史。
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <Input
            value={title}
            onChange={(event) => onTitleChange(event.target.value)}
            placeholder="例如：半导体中军 vs 跟风"
          />
          <div className="rounded-lg border p-3 text-sm">
            当前已选 {selectedContextCount} 张上下文卡片；若未勾选任何卡片，提交时会默认复制当前线程全部上下文。
          </div>
          <div className="flex items-center gap-3 rounded-lg border p-3">
            <Checkbox
              checked={includeCompareTargets}
              onCheckedChange={(checked) =>
                onIncludeCompareTargetsChange(Boolean(checked))
              }
            />
            <div>
              <p className="font-medium text-sm">继承当前 compare targets</p>
              <p className="text-muted-foreground text-xs">
                保留当前显式对比对象，方便直接继续比较研究。
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-lg border p-3">
            <Checkbox
              checked={pinImportedContexts}
              onCheckedChange={(checked) => onPinImportedContextsChange(Boolean(checked))}
            />
            <div>
              <p className="font-medium text-sm">置顶导入的上下文卡片</p>
              <p className="text-muted-foreground text-xs">
                让新线程优先展示这批分叉上下文。
              </p>
            </div>
          </div>
          <div className="space-y-2">
            <p className="font-medium text-sm">focus_type</p>
            <Select value={focusTypeOverride} onValueChange={onFocusTypeOverrideChange}>
              <SelectTrigger>
                <SelectValue placeholder="选择 focus_type" />
              </SelectTrigger>
              <SelectContent>
                {FOCUS_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit} disabled={isSubmitting}>
            {isSubmitting ? "分叉中..." : "创建分叉线程"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
