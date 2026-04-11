import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Radar,
  Shield,
  Target,
} from "lucide-react";
import { useTheme } from "next-themes";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { useAllPollTaskList } from "@/api/conversation";
import { useGetHomepageContext } from "@/api/homepage-context";
import {
  IconGroupDarkPng,
  IconGroupPng,
  MessageGroupDarkPng,
  MessageGroupPng,
  TrendDarkPng,
  TrendPng,
} from "@/assets/png";
import { AutoTrade, NewsPush, ResearchReport } from "@/assets/svg";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import TradingViewTickerTape from "@/components/tradingview/tradingview-ticker-tape";
import SvgIcon from "@/components/valuecell/icon/svg-icon";
import type { HomepageSignal, HomepageThemeItem } from "@/types/homepage-context";
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

const formatPercent = (value?: number | null) => {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
};

const getThemeStateClassName = (state?: string | null) => {
  if (state === "加强") return "bg-emerald-500/10 text-emerald-500";
  if (state === "活跃") return "bg-blue-500/10 text-blue-500";
  if (state === "观察") return "bg-orange-500/10 text-orange-500";
  return "bg-muted text-muted-foreground";
};

function SectionCard({
  title,
  description,
  icon,
  children,
}: {
  title: string;
  description: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border bg-background p-5">
      <div className="mb-4 flex items-start gap-3">
        <div className="rounded-xl bg-muted p-2">{icon}</div>
        <div>
          <p className="font-semibold text-lg">{title}</p>
          <p className="text-muted-foreground text-sm">{description}</p>
        </div>
      </div>
      {children}
    </section>
  );
}

function SignalBadges({ signals }: { signals: HomepageSignal[] }) {
  if (!signals.length) return null;
  return (
    <div className="mt-4 flex flex-wrap gap-2">
      {signals.map((signal) => (
        <Badge key={signal.label} variant="secondary">
          {signal.label} {signal.value ?? "--"}
        </Badge>
      ))}
    </div>
  );
}

function ThemeCard({ item }: { item: HomepageThemeItem }) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <p className="font-medium text-sm">{item.theme_name}</p>
            <Badge className={getThemeStateClassName(item.theme_state)}>
              {item.theme_state}
            </Badge>
          </div>
          <p className="mt-2 text-muted-foreground text-sm">{item.summary}</p>
        </div>
        <div className="text-right">
          <p className="font-semibold text-lg">{item.rank}</p>
          <p className="text-muted-foreground text-xs">优先级</p>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
        <span>涨跌幅 {formatPercent(item.metrics.change_value)}</span>
        <span>预期差 {item.expectation_gap_level}</span>
        <span>热度 {item.metrics.hot_count}</span>
      </div>

      {!!item.core_leaders_json.length && (
        <div className="mt-3 flex flex-wrap gap-2">
          {item.core_leaders_json.slice(0, 3).map((ticker) => (
            <Badge key={ticker} variant="outline">
              {ticker}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

function Home() {
  const { t, i18n } = useTranslation();
  const { resolvedTheme } = useTheme();
  const navigate = useNavigate();
  const [inputValue, setInputValue] = useState<string>("");

  const { data: allPollTaskList } = useAllPollTaskList();
  const { data: homepageContext, isLoading: homepageLoading } =
    useGetHomepageContext();

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
          {homepageLoading && !homepageContext ? (
            <div className="flex min-h-80 items-center justify-center">
              <Spinner className="size-6" />
            </div>
          ) : (
            <div className="space-y-4">
              <SectionCard
                title="市场总览"
                description="先看今天更适合进攻、轮动还是防守。"
                icon={<Radar className="size-5" />}
              >
                {homepageContext?.market_overview.available ? (
                  <>
                    <div className="flex flex-wrap items-center gap-3">
                      <p className="font-semibold text-2xl">
                        {homepageContext.market_overview.market_state}
                      </p>
                      {homepageContext.market_overview.confidence ? (
                        <Badge variant="secondary">
                          置信度 {homepageContext.market_overview.confidence}
                        </Badge>
                      ) : null}
                      {homepageContext.market_overview.score !== null ? (
                        <Badge variant="outline">
                          温度分 {homepageContext.market_overview.score}
                        </Badge>
                      ) : null}
                    </div>
                    <p className="mt-3 text-sm">
                      {homepageContext.market_overview.summary}
                    </p>
                    <p className="mt-2 text-muted-foreground text-sm">
                      {homepageContext.market_overview.action_hint}
                    </p>
                    <SignalBadges
                      signals={homepageContext.market_overview.signals}
                    />
                  </>
                ) : (
                  <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                    {homepageContext?.market_overview.empty_message ||
                      "暂无可用市场快照"}
                  </div>
                )}
              </SectionCard>

              <SectionCard
                title="情绪周期与最近轨迹"
                description="识别当前情绪阶段和最近几天的走向变化。"
                icon={<Activity className="size-5" />}
              >
                {homepageContext?.emotion_cycle.available ? (
                  <>
                    <div className="flex flex-wrap items-center gap-3">
                      <p className="font-semibold text-2xl">
                        {homepageContext.emotion_cycle.cycle_stage}
                      </p>
                      {homepageContext.emotion_cycle.trend_direction ? (
                        <Badge variant="secondary">
                          最近走势 {homepageContext.emotion_cycle.trend_direction}
                        </Badge>
                      ) : null}
                    </div>
                    <p className="mt-3 text-sm">
                      {homepageContext.emotion_cycle.summary}
                    </p>
                    <div className="mt-4 grid gap-3 md:grid-cols-5">
                      {homepageContext.emotion_cycle.stage_points.map((point) => (
                        <div
                          key={`${point.trading_date}-${point.cycle_stage}`}
                          className="rounded-xl border bg-card p-3"
                        >
                          <p className="text-muted-foreground text-xs">
                            {point.trading_date}
                          </p>
                          <p className="mt-1 font-medium text-sm">
                            {point.cycle_stage}
                          </p>
                          <p className="mt-2 text-muted-foreground text-xs">
                            阶段分 {point.stage_score}
                          </p>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                    {homepageContext?.emotion_cycle.empty_message ||
                      "暂无可用情绪周期数据"}
                  </div>
                )}
              </SectionCard>

              <SectionCard
                title="主流题材和板块趋势"
                description="聚焦 1 到 3 个当前更值得优先跟踪的方向。"
                icon={<Target className="size-5" />}
              >
                {homepageContext?.theme_focus.available ? (
                  <div className="grid gap-3 lg:grid-cols-3">
                    {homepageContext.theme_focus.items.map((item) => (
                      <ThemeCard key={item.theme_code} item={item} />
                    ))}
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                    {homepageContext?.theme_focus.empty_message ||
                      "暂无清晰主流题材"}
                  </div>
                )}
              </SectionCard>

              <SectionCard
                title={homepageContext?.action_framework.title || "今日操作框架"}
                description="把市场、情绪、题材和持仓放到同一个行动节奏里。"
                icon={<ArrowUpRight className="size-5" />}
              >
                {homepageContext?.action_framework.available ? (
                  <div className="grid gap-4 lg:grid-cols-2">
                    <div className="rounded-xl border bg-card p-4">
                      <p className="font-medium text-sm">今日优先动作</p>
                      <p className="mt-2 text-sm">
                        {homepageContext.action_framework.summary}
                      </p>
                      <div className="mt-3 space-y-2 text-muted-foreground text-sm">
                        {homepageContext.action_framework.focus_points.map((item) => (
                          <p key={item}>- {item}</p>
                        ))}
                      </div>
                    </div>
                    <div className="rounded-xl border bg-card p-4">
                      <p className="font-medium text-sm">今日避免事项</p>
                      <div className="mt-3 space-y-2 text-muted-foreground text-sm">
                        {homepageContext.action_framework.avoid_points.map((item) => (
                          <p key={item}>- {item}</p>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                    {homepageContext?.action_framework.empty_message ||
                      "暂无可用操作框架"}
                  </div>
                )}
              </SectionCard>

              <SectionCard
                title="自选观察"
                description="优先从观察池里识别重点观察、风险观察和主题联动。"
                icon={<ArrowDownRight className="size-5" />}
              >
                {homepageContext?.watchlist_observation.available ? (
                  <div className="grid gap-3 lg:grid-cols-2">
                    {homepageContext.watchlist_observation.items
                      .slice(0, 4)
                      .map((item) => (
                        <div
                          key={item.ticker}
                          className="rounded-xl border bg-card p-4"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <div>
                              <p className="font-medium text-sm">{item.display_name}</p>
                              <p className="text-muted-foreground text-xs">
                                {item.ticker}
                              </p>
                            </div>
                            <div className="text-right">
                              <Badge variant="secondary">{item.status}</Badge>
                              <p
                                className={`mt-2 text-xs ${
                                  (item.change_percent || 0) >= 0
                                    ? "text-emerald-500"
                                    : "text-red-500"
                                }`}
                              >
                                {formatPercent(item.change_percent)}
                              </p>
                            </div>
                          </div>
                          <p className="mt-3 text-sm">{item.reason}</p>
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
                    {homepageContext?.watchlist_observation.empty_message ||
                      "暂无自选观察数据"}
                  </div>
                )}
              </SectionCard>

              <PortfolioOverview
                showDailySummary={false}
                sectionTitle="持仓处理"
                sectionDescription="围绕已有持仓给出短周期动作建议，并保留录入、编辑、删除与诊断刷新能力。"
                className="p-0"
              />

              <SectionCard
                title="风控与分仓策略"
                description="先管仓位，再决定进攻节奏，避免因为情绪切换放大回撤。"
                icon={<Shield className="size-5" />}
              >
                <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
                  <div className="rounded-xl border bg-card p-4">
                    <p className="font-medium text-sm">仓位建议</p>
                    <p className="mt-3 text-sm">
                      {homepageContext?.risk_control.position_suggestion ||
                        "暂无可用仓位建议"}
                    </p>
                    <p className="mt-3 text-muted-foreground text-sm">
                      {homepageContext?.risk_control.summary}
                    </p>
                  </div>
                  <div className="rounded-xl border bg-card p-4">
                    <p className="font-medium text-sm">风险提示</p>
                    <div className="mt-3 space-y-2 text-muted-foreground text-sm">
                      {(homepageContext?.risk_control.signals || []).length ? (
                        homepageContext?.risk_control.signals.map((item) => (
                          <p key={item}>- {item}</p>
                        ))
                      ) : (
                        <p>暂无额外风险提示。</p>
                      )}
                    </div>
                  </div>
                </div>
              </SectionCard>
            </div>
          )}

          {allPollTaskList && allPollTaskList.length > 0 ? (
            <div className="mt-4">
              <AgentTaskCards tasks={allPollTaskList} />
            </div>
          ) : null}

          <div className="mt-4 space-y-6 rounded-2xl border bg-background p-6">
            <div>
              <h2 className="font-medium text-2xl text-foreground">
                深度分析与通用 Agent
              </h2>
              <p className="mt-2 text-muted-foreground text-sm">
                工作台优先服务“今天先看什么”，更深入的问题再进入聊天和通用 Agent。
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
