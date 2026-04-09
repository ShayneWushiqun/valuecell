import { useTheme } from "next-themes";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { useAllPollTaskList } from "@/api/conversation";
import {
  IconGroupDarkPng,
  IconGroupPng,
  MessageGroupDarkPng,
  MessageGroupPng,
  TrendDarkPng,
  TrendPng,
} from "@/assets/png";
import { AutoTrade, NewsPush, ResearchReport } from "@/assets/svg";
import TradingViewTickerTape from "@/components/tradingview/tradingview-ticker-tape";
import SvgIcon from "@/components/valuecell/icon/svg-icon";
import ChatInputArea from "../agent/components/chat-conversation/chat-input-area";
import { AgentSuggestionsList, AgentTaskCards, PortfolioOverview } from "./components";

const INDEX_SYMBOLS = [
  "FOREXCOM:SPXUSD",
  "NASDAQ:IXIC",
  "NASDAQ:NDX",
  "INDEX:HSI",
  "SSE:000001",
  "BINANCE:BTCUSDT",
  "BINANCE:ETHUSDT",
];

function Home() {
  const { t, i18n } = useTranslation();
  const { resolvedTheme } = useTheme();
  const navigate = useNavigate();
  const [inputValue, setInputValue] = useState<string>("");

  const { data: allPollTaskList } = useAllPollTaskList();

  const handleAgentClick = (agentId: string) => {
    navigate(`/agent/${agentId}`);
  };

  const isDark = resolvedTheme === "dark";

  const suggestions = [
    {
      id: "ResearchAgent",
      title: t("home.suggestions.research.title"),
      icon: <SvgIcon name={ResearchReport} />,
      description: t("home.suggestions.research.description"),
      bgColor: isDark
        ? "bg-gradient-to-r from-[#111827]/80 from-[5.05%] to-[#1D4ED8]/35 to-[100%]"
        : "bg-gradient-to-r from-[#FFFFFF]/70 from-[5.05%] to-[#E7EFFF]/70 to-[100%]",
      decorativeGraphics: (
        <img src={isDark ? IconGroupDarkPng : IconGroupPng} alt="IconGroup" />
      ),
    },
    {
      id: "StrategyAgent",
      title: t("home.suggestions.strategy.title"),
      icon: <SvgIcon name={AutoTrade} />,
      description: t("home.suggestions.strategy.description"),
      bgColor: isDark
        ? "bg-gradient-to-r from-[#111827]/80 from-[5.05%] to-[#7C3AED]/30 to-[100%]"
        : "bg-gradient-to-r from-[#FFFFFF]/70 from-[5.05%] to-[#EAE8FF]/70 to-[100%]",
      decorativeGraphics: (
        <img src={isDark ? TrendDarkPng : TrendPng} alt="Trend" />
      ),
    },
    {
      id: "NewsAgent",
      title: t("home.suggestions.news.title"),
      icon: <SvgIcon name={NewsPush} />,
      description: t("home.suggestions.news.description"),
      bgColor: isDark
        ? "bg-gradient-to-r from-[#111827]/80 from-[5.05%] to-[#DB2777]/25 to-[100%]"
        : "bg-gradient-to-r from-[#FFFFFF]/70 from-[5.05%] to-[#FFE7FD]/70 to-[100%]",
      decorativeGraphics: (
        <img
          src={isDark ? MessageGroupDarkPng : MessageGroupPng}
          alt="MessageGroup"
        />
      ),
    },
  ];

  return (
    <div className="flex h-full min-w-[800px] flex-col gap-3">
      <section className="flex w-full flex-1 flex-col gap-4 rounded-lg bg-card p-4">
        <TradingViewTickerTape
          symbols={INDEX_SYMBOLS}
          theme={resolvedTheme === "dark" ? "dark" : "light"}
          locale={i18n.language}
        />

        <div className="scroll-container flex-1">
          <PortfolioOverview />

          {allPollTaskList && allPollTaskList.length > 0 ? (
            <div className="mt-4">
              <AgentTaskCards tasks={allPollTaskList} />
            </div>
          ) : null}

          <div className="mt-4 space-y-6 rounded-2xl border bg-background p-6">
            <div>
              <h2 className="font-medium text-2xl text-foreground">
                {t("home.hello")}
              </h2>
              <p className="mt-2 text-muted-foreground text-sm">
                阶段一首页已优先展示持仓诊断、每日摘要和自选入口，聊天与 Agent 入口继续保留。
              </p>
            </div>

            <ChatInputArea
              className="w-full"
              value={inputValue}
              onChange={(value) => setInputValue(value)}
              onSend={() =>
                navigate("/agent/ValueCellAgent", {
                  state: {
                    inputValue,
                  },
                })
              }
            />

            <AgentSuggestionsList
              suggestions={suggestions.map((suggestion) => ({
                ...suggestion,
                onClick: () => handleAgentClick(suggestion.id),
              }))}
            />
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;
