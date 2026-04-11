import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Radar,
  Shield,
  Target,
} from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useMemo, useState } from "react";
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
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import SvgIcon from "@/components/valuecell/icon/svg-icon";
import type {
  HomepageEmotionCycle,
  HomepageMarketOverview,
  HomepageSignal,
  HomepageStagePoint,
  HomepageThemeItem,
} from "@/types/homepage-context";
import ChatInputArea from "../agent/components/chat-conversation/chat-input-area";
import { AgentSuggestionsList, AgentTaskCards, PortfolioOverview } from "./components";

const formatPercent = (value?: number | null) => {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
};

const getThemeStateClassName = (state?: string | null) => {
  if (state === "加强") return "bg-emerald-500/10 text-emerald-500";
  if (state === "活跃") return "bg-blue-500/10 text-blue-500";
  if (state === "分歧") return "bg-orange-500/10 text-orange-500";
  if (state === "退潮") return "bg-red-500/10 text-red-500";
  return "bg-muted text-muted-foreground";
};

const getParticipationBadgeClassName = (enabled: boolean) =>
  enabled
    ? "bg-emerald-500/10 text-emerald-500"
    : "bg-orange-500/10 text-orange-500";

const formatEmotionTickLabel = (tradingDate: string) => {
  if (tradingDate.length !== 8) return tradingDate;
  return `${tradingDate.slice(4, 6)}/${tradingDate.slice(6, 8)}`;
};

const shouldRenderEmotionTickLabel = (index: number, total: number) => {
  if (total <= 10) return true;
  if (index === 0 || index === total - 1) return true;
  if (total <= 20) return index % 2 === 0;
  return index % 4 === 0;
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

function AShareMarketStrip({
  marketOverview,
}: {
  marketOverview?: HomepageMarketOverview;
}) {
  const breadthItems = marketOverview?.breadth_items || [];
  const indexQuotes = marketOverview?.index_quotes || [];

  return (
    <section className="rounded-2xl border bg-background p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="font-semibold text-base">A股全局行情</p>
          <p className="text-muted-foreground text-sm">
            优先看 A 股核心指数和市场宽度，不再用泛市场 ticker 占据顶部。
          </p>
        </div>
        {marketOverview?.market_state ? (
          <Badge variant="secondary">当前环境 {marketOverview.market_state}</Badge>
        ) : null}
      </div>

      <div className="grid gap-3 xl:grid-cols-[2fr_1.2fr]">
        <div className="grid gap-3 md:grid-cols-5">
          {indexQuotes.map((item) => (
            <div key={item.ticker} className="rounded-xl border bg-card p-3">
              <p className="text-muted-foreground text-xs">{item.label}</p>
              <p className="mt-2 font-semibold text-lg">{item.price || "--"}</p>
              <p
                className={`mt-1 text-xs ${
                  (item.change_percent || 0) >= 0
                    ? "text-emerald-500"
                    : "text-red-500"
                }`}
              >
                {formatPercent(item.change_percent)}
              </p>
            </div>
          ))}
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          {(breadthItems.length ? breadthItems : marketOverview?.signals || []).map(
            (item) => (
              <div key={item.label} className="rounded-xl border bg-card p-3">
                <p className="text-muted-foreground text-xs">{item.label}</p>
                <p className="mt-2 font-semibold text-lg">{item.value ?? "--"}</p>
              </div>
            ),
          )}
        </div>
      </div>
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

function EmotionCurve({
  emotionCycle,
}: {
  emotionCycle?: HomepageEmotionCycle;
}) {
  const [windowDays, setWindowDays] = useState(20);
  const [hoveredPoint, setHoveredPoint] = useState<HomepageStagePoint | null>(null);
  const defaultWindowDays =
    emotionCycle?.default_window_days &&
    [10, 20, 30].includes(emotionCycle.default_window_days)
      ? emotionCycle.default_window_days
      : 20;

  useEffect(() => {
    setWindowDays((current) => (current === 20 ? defaultWindowDays : current));
  }, [defaultWindowDays]);

  const visiblePoints = useMemo(() => {
    const points = emotionCycle?.stage_points || [];
    return points.slice(-windowDays);
  }, [emotionCycle?.stage_points, windowDays]);

  const polylinePoints = useMemo(() => {
    if (!visiblePoints.length) return "";
    const width = 760;
    const height = 180;
    const step = visiblePoints.length > 1 ? width / (visiblePoints.length - 1) : width;
    return visiblePoints
      .map((point, index) => {
        const x = index * step;
        const y = height - (Math.max(0, Math.min(100, point.stage_score)) / 100) * height;
        return `${x},${y}`;
      })
      .join(" ");
  }, [visiblePoints]);

  if (!emotionCycle?.available) {
    return (
      <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
        {emotionCycle?.empty_message || "暂无可用情绪周期数据"}
      </div>
    );
  }

  if (!visiblePoints.length) {
    return (
      <div className="rounded-xl border border-dashed p-4 text-muted-foreground text-sm">
        {emotionCycle.empty_message || "暂无足够的情绪轨迹数据可绘制曲线"}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <p className="font-semibold text-2xl">{emotionCycle.cycle_stage}</p>
          {emotionCycle.trend_direction ? (
            <Badge variant="secondary">最近走势 {emotionCycle.trend_direction}</Badge>
          ) : null}
        </div>

        <div className="flex items-center gap-2">
          {[10, 20, 30].map((days) => (
            <Button
              key={days}
              size="sm"
              variant={windowDays === days ? "default" : "secondary"}
              onClick={() => setWindowDays(days)}
            >
              {days}天
            </Button>
          ))}
        </div>
      </div>

      <p className="text-sm">{emotionCycle.summary}</p>

      <div className="rounded-xl border bg-card p-4">
        <svg viewBox="0 0 760 240" className="h-72 w-full">
          <line x1="0" y1="180" x2="760" y2="180" stroke="currentColor" opacity="0.15" />
          <line x1="0" y1="0" x2="0" y2="180" stroke="currentColor" opacity="0.15" />
          <line x1="0" y1="180" x2="760" y2="180" stroke="currentColor" opacity="0.08" />
          <line x1="0" y1="135" x2="760" y2="135" stroke="currentColor" opacity="0.05" />
          <line x1="0" y1="90" x2="760" y2="90" stroke="currentColor" opacity="0.08" />
          <line x1="0" y1="45" x2="760" y2="45" stroke="currentColor" opacity="0.05" />
          <line x1="0" y1="0" x2="760" y2="0" stroke="currentColor" opacity="0.08" />
          <text x="6" y="12" fontSize="11" fill="currentColor" opacity="0.55">
            100
          </text>
          <text x="6" y="57" fontSize="11" fill="currentColor" opacity="0.55">
            75
          </text>
          <text x="6" y="102" fontSize="11" fill="currentColor" opacity="0.55">
            50
          </text>
          <text x="6" y="147" fontSize="11" fill="currentColor" opacity="0.55">
            25
          </text>
          <text x="6" y="192" fontSize="11" fill="currentColor" opacity="0.55">
            0
          </text>
          <polyline
            fill="none"
            stroke="rgb(59 130 246)"
            strokeWidth="3"
            points={polylinePoints}
          />
          {visiblePoints.map((point, index) => {
            const step = visiblePoints.length > 1 ? 760 / (visiblePoints.length - 1) : 760;
            const x = index * step;
            const y = 180 - (Math.max(0, Math.min(100, point.stage_score)) / 100) * 180;
            return (
              <g
                key={`${point.trading_date}-${point.stage_score}`}
                onMouseEnter={() => setHoveredPoint(point)}
                onMouseLeave={() => setHoveredPoint(null)}
              >
                <circle cx={x} cy={y} r="5" fill="rgb(59 130 246)" />
                <text
                  x={x}
                  y="206"
                  textAnchor="middle"
                  fontSize="11"
                  fill="currentColor"
                  opacity="0.7"
                >
                  {shouldRenderEmotionTickLabel(index, visiblePoints.length)
                    ? formatEmotionTickLabel(point.trading_date)
                    : ""}
                </text>
              </g>
            );
          })}
        </svg>

        <div className="mt-3 rounded-xl bg-muted/40 p-4 text-sm">
          {hoveredPoint ? (
            <div className="grid gap-2 md:grid-cols-2">
              <p>日期：{hoveredPoint.trading_date}</p>
              <p>情绪阶段：{hoveredPoint.cycle_stage}</p>
              <p>情绪分数：{hoveredPoint.stage_score}</p>
              <p>涨停数：{hoveredPoint.up_limit_count ?? "--"}</p>
              <p>跌停数：{hoveredPoint.down_limit_count ?? "--"}</p>
              <p>炸板数：{hoveredPoint.broken_limit_count ?? "--"}</p>
              <p>最高连板：{hoveredPoint.highest_board ?? "--"}</p>
              <p>当日操作提示：{hoveredPoint.action_hint || "--"}</p>
            </div>
          ) : (
            <p className="text-muted-foreground">
              鼠标移到曲线节点上，可查看日期、情绪分数、涨跌停、炸板、最高连板和当日操作提示。
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function ThemeRow({ item }: { item: HomepageThemeItem }) {
  const [showEtfDetails, setShowEtfDetails] = useState(false);

  return (
    <div className="rounded-xl border bg-card p-3">
      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_220px] xl:items-start">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-medium text-sm">{item.theme_name}</p>
            <Badge className={getThemeStateClassName(item.theme_state)}>
              {item.theme_state}
            </Badge>
            <Badge variant="outline">{item.trend_state}</Badge>
            <Badge className={getParticipationBadgeClassName(item.is_suitable_for_direct_participation)}>
              {item.is_suitable_for_direct_participation ? "适合直接参与" : "更适合观察"}
            </Badge>
          </div>

          <div className="flex flex-wrap gap-3 text-muted-foreground text-xs">
            <span>涨跌幅 {formatPercent(item.metrics.change_value)}</span>
            <span>热度 {item.hot_level}</span>
            <span>预期差 {item.expectation_gap_level}</span>
            <span>{item.preferred_market}</span>
          </div>

          <p className="overflow-hidden text-ellipsis whitespace-nowrap text-muted-foreground text-xs leading-5">
            {item.participation_hint}
          </p>

          <div className="flex flex-wrap gap-2">
            {(item.core_leaders_json || []).slice(0, 3).map((ticker) => (
              <Badge key={ticker} variant="outline">
                {ticker}
              </Badge>
            ))}
          </div>
        </div>

        <div className="rounded-xl bg-muted/40 p-3 text-sm">
          <p className="font-medium text-xs">代表股</p>
          <p className="mt-1 text-sm">{item.primary_representative || "暂无代表股"}</p>
          <p className="mt-2 overflow-hidden text-ellipsis whitespace-nowrap text-muted-foreground text-xs leading-5">
            {item.summary}
          </p>
          {item.etf_hint ? (
            <div className="mt-2">
              <Button
                size="sm"
                variant="ghost"
                className="h-7 px-2 text-xs"
                onClick={() => setShowEtfDetails((value) => !value)}
              >
                {showEtfDetails ? "收起ETF提示" : "展开ETF提示"}
              </Button>
              {showEtfDetails ? (
                <div className="mt-2 rounded-lg border border-dashed p-2.5">
                  <p className="font-medium text-xs">{item.etf_hint.title}</p>
                  <p className="mt-1.5 text-muted-foreground text-xs leading-5">
                    {item.etf_hint.summary}
                  </p>
                  <div className="mt-1.5 flex items-start gap-2 text-orange-500 text-xs">
                    <AlertTriangle className="mt-0.5 size-3.5" />
                    <span>{item.etf_hint.risk_hint}</span>
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function Home() {
  const { t } = useTranslation();
  const { resolvedTheme } = useTheme();
  const navigate = useNavigate();
  const [inputValue, setInputValue] = useState<string>("");
  const [showAllThemes, setShowAllThemes] = useState(false);

  const { data: allPollTaskList } = useAllPollTaskList();
  const { data: homepageContext, isLoading: homepageLoading } =
    useGetHomepageContext();

  const handleAgentClick = (agentId: string) => {
    navigate(`/agent/${agentId}`);
  };

  const isDark = resolvedTheme === "dark";
  const themeItems = homepageContext?.theme_focus.items || [];
  const visibleThemeItems = showAllThemes ? themeItems : themeItems.slice(0, 6);

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
        <div className="scroll-container flex-1">
          {homepageLoading && !homepageContext ? (
            <div className="flex min-h-80 items-center justify-center">
              <Spinner className="size-6" />
            </div>
          ) : (
            <div className="space-y-4">
              <AShareMarketStrip marketOverview={homepageContext?.market_overview} />

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
                description="用 0-100 情绪曲线看最近 10/20/30 天的变化，而不是只看阶段卡片。"
                icon={<Activity className="size-5" />}
              >
                <EmotionCurve emotionCycle={homepageContext?.emotion_cycle} />
              </SectionCard>

              <SectionCard
                title="主流题材和板块趋势"
                description="默认展示更多热门方向，过滤 ST 干扰，并明确是否适合直接参与。"
                icon={<Target className="size-5" />}
              >
                {homepageContext?.theme_focus.available ? (
                  <div className="space-y-3">
                    <div className="grid gap-3 xl:grid-cols-2">
                      {visibleThemeItems.map((item) => (
                        <ThemeRow key={item.theme_code} item={item} />
                      ))}
                    </div>
                    {themeItems.length > 6 ? (
                      <div className="flex justify-center">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setShowAllThemes((value) => !value)}
                        >
                          {showAllThemes
                            ? "收起剩余题材"
                            : `展开更多题材（还有 ${themeItems.length - 6} 个）`}
                        </Button>
                      </div>
                    ) : null}
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
                  <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr_1fr]">
                    <div className="rounded-xl border bg-card p-4">
                      <p className="font-medium text-sm">今日优先动作</p>
                      <p className="mt-2 text-sm">
                        {homepageContext.action_framework.summary}
                      </p>
                      <div className="mt-3 space-y-2 text-muted-foreground text-sm">
                        {(homepageContext.action_framework.focus_points || []).map((item) => (
                          <p key={item}>- {item}</p>
                        ))}
                      </div>
                    </div>
                    <div className="rounded-xl border bg-card p-4">
                      <p className="font-medium text-sm">今日避免事项</p>
                      <div className="mt-3 space-y-2 text-muted-foreground text-sm">
                        {(homepageContext.action_framework.avoid_points || []).map((item) => (
                          <p key={item}>- {item}</p>
                        ))}
                      </div>
                    </div>
                    <div className="rounded-xl border bg-card p-4">
                      <p className="font-medium text-sm">默认风险偏好</p>
                      <div className="mt-3 space-y-2 text-muted-foreground text-sm">
                        {(homepageContext.action_framework.participation_preferences || []).map(
                          (item) => (
                            <p key={item}>- {item}</p>
                          ),
                        )}
                      </div>
                      {homepageContext.action_framework.etf_strategy_hint ? (
                        <div className="mt-4 rounded-lg border border-dashed p-3">
                          <p className="font-medium text-xs">ETF 替代参与提示</p>
                          <p className="mt-2 text-muted-foreground text-xs">
                            {homepageContext.action_framework.etf_strategy_hint}
                          </p>
                        </div>
                      ) : null}
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
                description="首页只保留重点自选 3 到 5 条，完整观察池收在右侧轻入口里。"
                icon={<ArrowDownRight className="size-5" />}
              >
                {homepageContext?.watchlist_observation.available ? (
                  <div className="grid gap-3 lg:grid-cols-2">
                    {(homepageContext.watchlist_observation.items || [])
                      .slice(0, 5)
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
                          <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                            <span>{item.tradeability_state}</span>
                            <span>· 预期差 {item.expectation_gap_level}</span>
                            <span>· {item.role_label}</span>
                            <span>· 趋势 {item.trend_quality}</span>
                          </div>
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
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Badge variant="secondary">
                        总仓位 {homepageContext?.risk_control.total_position_range || "--"}
                      </Badge>
                      <Badge variant="outline">
                        单票 {homepageContext?.risk_control.single_position_range || "--"}
                      </Badge>
                      <Badge variant="outline">
                        节奏 {homepageContext?.risk_control.build_strategy || "--"}
                      </Badge>
                    </div>
                    <p className="mt-3 text-sm">
                      {homepageContext?.risk_control.position_suggestion ||
                        "暂无可用仓位建议"}
                    </p>
                    <p className="mt-3 text-muted-foreground text-sm">
                      {homepageContext?.risk_control.summary}
                    </p>
                    <p className="mt-3 text-muted-foreground text-sm">
                      {homepageContext?.risk_control.theme_concentration_hint}
                    </p>
                  </div>
                  <div className="rounded-xl border bg-card p-4">
                    <p className="font-medium text-sm">风险提示</p>
                    <div className="mt-3 space-y-2 text-muted-foreground text-sm">
                      {(homepageContext?.risk_control.signals || []).length ? (
                        (homepageContext?.risk_control.signals || []).map((item) => (
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
