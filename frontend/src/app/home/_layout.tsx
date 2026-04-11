import { Plus } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Outlet } from "react-router";
import { Button } from "@/components/ui/button";
import { StockList, StockSearchModal } from "./components";

export default function HomeLayout() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-1 flex-col gap-4 overflow-hidden bg-muted py-4 pr-4 pl-2">
      <div className="rounded-2xl bg-card px-6 py-5">
        <h1 className="font-medium text-3xl text-foreground">A股短周期工作台</h1>
        <p className="mt-2 text-muted-foreground text-sm">
          按市场总览、情绪周期、主流题材、自选观察和持仓处理组织每天的决策节奏。
        </p>
      </div>

      <div className="flex flex-1 gap-3 overflow-hidden">
        <main className="scroll-container flex-1 rounded-lg bg-card">
          <Outlet />
        </main>

        <aside className="flex w-80 flex-col overflow-hidden rounded-lg bg-card">
          <StockList />

          <StockSearchModal>
            <Button variant="secondary" className="mx-5 mb-6 font-bold text-sm">
              <Plus size={16} />
              {t("home.stock.add")}
            </Button>
          </StockSearchModal>
        </aside>
      </div>
    </div>
  );
}
