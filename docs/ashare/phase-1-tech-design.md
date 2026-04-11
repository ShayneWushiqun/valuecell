# 阶段一技术方案

## 1. 目标

在当前代码基础上，最小增量实现一个：

`以市场温度、主线题材、自选观察和持仓处理为核心的 A 股短周期首页。`

阶段一不是要把全部短周期能力一次性做完，而是先把首页工作台搭起来，让用户每天打开就能知道：

- 今天市场大致怎么做
- 当前情绪周期处在哪个阶段
- 今天先看哪些方向
- 哪些自选值得看
- 哪些持仓要处理

## 2. 当前基础能力盘点

### 2.1 已有能力

- A 股 ticker 识别、实时价格、历史价格、新闻回退能力
  位置：`python/valuecell/adapters/assets/ashare_provider.py`
- A 股基本面与财务报表能力
  位置：`python/tradingagents/dataflows/tushare_finance.py`
- 自选股和股票搜索能力
  位置：`python/valuecell/server/api/routers/watchlist.py`
- 首页与股票相关前端页面
  位置：`frontend/src/app/home/`
- 已有持仓、诊断、每日摘要原型
  位置：`python/valuecell/server/services/portfolio/`
  和 `frontend/src/app/home/components/portfolio-overview.tsx`
- 已有短周期数据接入层与语义服务原型
  位置：`python/valuecell/adapters/assets/tushare_adapter.py`
  、`python/valuecell/adapters/assets/tushare_short_cycle_gateway.py`
  、`python/valuecell/server/services/assets/`

### 2.1.1 当前已落地的短周期后端能力

截至当前这轮实现，后端已经先落了阶段一的数据与语义基础：

- 数据接入层：
  - 已为 `daily`、`daily_basic`、`daily_info`、`stk_limit`
  - `limit_list_d`、`kpl_list`
  - `ths_index`、`ths_daily`、`ths_member`
  - `moneyflow_ind_ths`、`moneyflow_ind_dc`、`moneyflow`
  - `ths_hot`、`disclosure_date`、`stk_holdertrade`、`share_float`
  - `top_list`、`top_inst`、`forecast_vip`、`express_vip`、`tdx_index`
    提供了统一访问入口
- 聚合层：
  - 已增加 `TushareShortCycleGateway`
  - 已按市场脉冲、题材聚焦、个股观察提供 bundle
- 服务层：
  - 已增加 `ShortCycleDataService`
  - 已增加 `MarketPulseService`
  - 已增加 `EmotionCycleService`
  - 已增加 `ThemeFocusService`
  - 已增加 `HomepageContextService`
- API 层：
  - 已增加 `/api/v1/homepage/context`
- 前端层：
  - 首页第一屏已切换为短周期工作台布局
  - 聊天区和通用 Agent 已下沉到次要区域
  - 右侧自选区已改成带观察状态和原因的观察池

当前这些能力的定位是：

- 先把短周期后端语义基础铺好
- 让首页上下文、自选观察、持仓动作和风控模块可以直接复用
- 首页工作台结构已收敛，但语义服务仍未完全闭环

### 2.2 当前缺口

当前缺的不是持仓模型本身，而是短周期语义层：

- 首页字段口径仍需要继续校准
- 自选观察还没有独立服务层
- 持仓建议仍偏“研究和风险说明”
- 缺少对预期差、持续性和可交易性的统一表达
- 缺少对“核心票优先、弱票降权”的统一表达

## 2.3 当前数据基线

阶段一默认建立在：

- `Tushare 6000 积分`
- `个人使用`
- `非商业化`
- `不购买独立权限`

之上。

因此阶段一实现时：

- 应优先使用 [Tushare 6000 积分接口映射](./tushare-6000-interface-map.md)
- 不要直接依赖新闻、公告全文、政策法规、研报、实时分钟
- 不要直接依赖 8000 积分以上接口

## 3. 总体思路

阶段一采用：

`现有数据复用 + 轻量规则组织 + 结构化摘要输出 + 首页重新编排`

核心思路是：

1. 复用已有价格、自选、持仓和摘要能力
2. 增加一层轻量“短周期首页上下文”组织层
3. 在首页上下文中加入预期差、持续性和可交易性标签
4. 生成适合首页展示的市场语境和重点内容
5. 在前端把聊天入口降级，把工作台升为主视觉

当前这一思路已经落了一版：

- `homepage_context_service.py` 负责聚合市场脉冲、情绪周期、题材聚焦、持仓与自选
- 前端首页已真实消费聚合 API
- 每个区块都支持空数据降级态，而不是伪造结论

首页上下文的组织顺序建议固定为：

1. 市场总览
2. 情绪周期及历史轨迹
3. 主线题材与板块趋势
4. 今日操作框架
5. 个股观察和持仓处理
6. 风控与分仓

## 4. 阶段一架构

### 4.1 分层

#### 数据层

- A 股价格和基础行情
- 自选股数据
- 持仓和诊断数据
- 基础新闻和公告摘要

#### 上下文组装层

- 市场快照组装
- 情绪周期快照和轨迹组装
- 主线方向归纳
- 自选观察整理
- 持仓处理整理
- 可交易性和流动性风险整理
- 风控与分仓建议整理

#### 生成层

- 今日摘要生成
- 首页卡片生成
- 建议卡压缩

#### 前端展示层

- 首页短周期工作台
- 自选观察区
- 持仓处理区

## 5. 建议的数据对象

阶段一不要求一次性新增大量数据库实体。

优先建议在现有持仓和摘要基础上，引入以下轻量对象或结构化返回。

### 5.1 `MarketPulseSnapshot`

建议字段：

- `trading_date`
- `market_state`
- `summary`
- `confidence`
- `action_hint`
- `signals_json`

字段含义：

- `market_state`：进攻 / 轮动 / 震荡 / 退潮 / 修复
- `summary`：面向用户的一句话描述
- `action_hint`：今天更适合追强、低吸、观察或防守

阶段一可以先做成动态聚合对象，不强制立刻落库。

### 5.2 `EmotionCycleSnapshot`

建议字段：

- `trading_date`
- `cycle_stage`
- `stage_score`
- `summary`
- `action_hint`
- `signals_json`

字段含义：

- `cycle_stage`：冰点 / 修复试错 / 主升发酵 / 高潮一致 / 分歧 / 退潮
- `stage_score`：用于表达阶段强弱程度
- `action_hint`：当前阶段更适合的操作方式

### 5.3 `EmotionCycleTimeline`

建议字段：

- `window_days`
- `stage_points_json`
- `trend_direction`
- `turning_points_json`

字段含义：

- `window_days`：建议默认 5 到 10 个交易日
- `trend_direction`：上行 / 横向 / 下行
- `turning_points_json`：记录阶段切换点

### 5.4 `ThemeFocusSnapshot`

建议字段：

- `trading_date`
- `theme_name`
- `theme_state`
- `summary`
- `representative_tickers_json`
- `rank`
- `expectation_gap_level`
- `core_leaders_json`
- `core_institutions_json`

字段含义：

- `theme_state`：加强 / 活跃 / 观察 / 退潮
- `summary`：为什么它今天值得看
- `expectation_gap_level`：高 / 中 / 低，用于描述当前预期是否已被打满

阶段一也可以先做成聚合对象，不要求先建复杂主题实体。

### 5.5 `SectorTrendSnapshot`

建议字段：

- `sector_name`
- `trend_state`
- `change_window`
- `summary`

字段含义：

- `trend_state`：加强 / 横盘 / 分歧 / 走弱
- `change_window`：建议使用近 3 到 5 日

### 5.6 `WatchlistObservation`

建议字段：

- `ticker`
- `display_name`
- `change_pct`
- `observation_state`
- `reason`
- `linked_theme`
- `tradeability_state`
- `expectation_gap_level`
- `role_label`
- `trend_quality`

字段含义：

- `observation_state`：普通观察 / 重点观察 / 风险观察
- `reason`：一句话说明为什么今天值得看
- `tradeability_state`：可观察 / 可低吸 / 谨慎追高 / 流动性风险
- `role_label`：龙头 / 中军 / 跟风 / 弱势
- `trend_quality`：顺势 / 震荡 / 拖沓 / 走弱

### 5.7 `HoldingActionCard`

建议基于现有持仓诊断对象补齐或统一以下字段：

- `ticker`
- `action`
- `risk_level`
- `summary`
- `reasons_json`
- `time_horizon`
- `expectation_state`
- `tradeability_state`
- `liquidity_risk`
- `role_label`
- `trend_quality`
- `updated_at`

字段含义：

- `time_horizon`：建议适用周期，例如 5、10、20 个交易日
- `expectation_state`：延续 / 观察 / 证伪风险
- `tradeability_state`：可持有 / 谨慎加仓 / 仅适合持有 / 流动性风险
- `role_label`：龙头 / 中军 / 跟风 / 弱势
- `trend_quality`：顺势 / 震荡 / 拖沓 / 走弱

### 5.8 `TradeabilityHint`

阶段一建议补充一个轻量的可交易性对象，用于首页和持仓卡片展示。

建议字段：

- `ticker`
- `state`
- `summary`
- `near_limit_up`
- `near_limit_down`

用途：

- 提示当前是否接近涨停，不适合追买
- 提示当前是否存在跌停或接近跌停的流动性风险

### 5.9 `RiskControlPlan`

阶段一建议补充一个轻量风控对象，用于首页直接展示。

建议字段：

- `trading_date`
- `total_position_range`
- `single_position_range`
- `build_strategy`
- `theme_concentration_hint`
- `summary`

字段含义：

- `total_position_range`：例如 2-4 成、4-6 成、6-8 成
- `single_position_range`：例如单票不超过 1 成、2 成
- `build_strategy`：试错仓 / 分批建仓 / 确认后加仓 / 防守为主

## 6. 后端服务建议

阶段一优先复用已有 `portfolio` 服务，不建议重造整套模块。

建议补充或新增以下轻量服务：

- `market_pulse_service.py`
- `emotion_cycle_service.py`
- `theme_focus_service.py`
- `risk_control_service.py`
- `homepage_context_service.py`

职责如下：

### 6.1 `market_pulse_service`

负责：

- 组织市场状态
- 生成市场温度卡
- 输出简短市场动作建议

阶段一允许基于轻量规则实现，不要求复杂模型。

建议主接口：

- `daily_info`
- `limit_list_d`
- `kpl_list`
- `daily`

### 6.2 `theme_focus_service`

负责：

- 生成当日重点方向
- 输出每个方向的一句话说明
- 为首页和摘要提供题材数据

阶段一允许先从有限数据、手工规则或轻量归纳做起。

建议主接口：

- `ths_index`
- `ths_daily`
- `ths_member`
- `moneyflow_ind_ths`
- `moneyflow_ind_dc`
- `kpl_list`
- `ths_hot`

### 6.3 `emotion_cycle_service`

负责：

- 识别当前情绪周期阶段
- 生成最近一段时间的周期轨迹
- 输出当前阶段的操作建议

说明：

- 情绪周期建议采用 6 阶段模型
- 阶段一允许使用轻量规则，不要求过度复杂的统计模型

建议主接口：

- `daily_info`
- `limit_list_d`
- `kpl_list`
- `ths_hot`

### 6.4 `risk_control_service`

负责：

- 根据市场状态、情绪周期和主线清晰度，给出基础仓位建议
- 输出总仓位、单票仓位和分批建仓提示

说明：

- 本服务不需要直接调用 Tushare
- 应依赖 `market_pulse_service`、`emotion_cycle_service` 和
  `theme_focus_service` 的结果

### 6.5 `homepage_context_service`

负责把以下内容聚合到一个首页上下文中：

- 市场温度
- 情绪周期与时间轨迹
- 今日摘要
- 重点题材
- 板块趋势
- 自选观察
- 持仓处理
- 预期差和可交易性提示
- 核心票优先级提示
- 风控与分仓建议

这样前端可以少做拼接逻辑。

说明：

- 首页聚合层不应直接重复请求 Tushare
- 应优先聚合上游服务结果，减少重复调用

### 6.6 自选观察与持仓处理的数据来源

当前阶段一的自选观察和持仓处理建议优先使用：

- `daily`
- `daily_basic`
- `moneyflow`
- `stk_limit`
- `limit_list_d`
- `ths_member`
- `ths_hot`
- `disclosure_date`
- `stk_holdertrade`
- `share_float`

如果阶段一希望最小可用，可以分两批接入：

1. 先接：
   - `daily`
   - `daily_basic`
   - `moneyflow`
   - `stk_limit`
   - `limit_list_d`
   - `ths_member`
2. 再补：
   - `ths_hot`
   - `disclosure_date`
   - `stk_holdertrade`
   - `share_float`

## 7. 诊断语义改造建议

阶段一最关键的不是再加更多字段，而是调整已有诊断的语义。

### 7.1 旧语义

偏研究型表达，例如：

- 基本面仍稳定
- 建议继续关注公司后续经营情况

### 7.2 新语义

偏短周期表达，例如：

- 当前仍可持有，观察 5 到 10 个交易日
- 所在方向走弱，建议先减仓等待修复
- 量价未破坏，但不适合追涨

### 7.3 技术要求

现有持仓诊断结构应尽量支持：

- 主动作
- 时间窗
- 风险等级
- 一到两条关键理由
- 预期状态
- 可交易性提示
- 角色标签
- 趋势质量

如果现有字段不足，可优先通过文本模板和聚合逻辑补齐语义，不必立即重构数据库。

### 7.4 A 股涨跌停约束

阶段一虽然不做高精度盘口系统，但技术设计必须预留对 A 股可交易性的表达。

至少要能支持以下语义：

- 这只票当前更适合持有，不适合追买
- 这只票接近涨停，追高性价比低
- 这只票存在跌停或接近跌停的流动性风险
- 这只票短期大跌，但预期未完全证伪，先观察修复窗口

如果阶段一拿不到完整盘口数据，可以先基于：

- 当日涨跌幅
- 是否接近涨跌停价格
- 最近几日强弱状态

做轻量判断。

### 7.5 核心票优先规则

阶段一建议在首页上下文层引入轻量优先级规则：

- 龙头和中军默认优先展示
- 趋势顺、承接强的票优先于拖沓弱票
- 跟风和弱势票默认降权

如果阶段一拿不到完整资金席位数据，可以先基于：

- 涨跌幅和趋势延续性
- 成交量和换手变化
- 是否反复进入重点观察
- 是否被归为题材代表股

做轻量角色判断。

## 8. 首页生成链路

建议阶段一采用固定流水线，而不是复杂自治 Agent。

### 8.1 流程

1. 拉取市场基础快照
2. 生成市场温度卡
3. 生成情绪周期卡和最近轨迹
4. 整理重点题材、板块和方向
5. 为重点方向补充预期差标签
6. 拉取用户自选并生成观察状态
7. 为自选和持仓补充可交易性提示
8. 拉取用户持仓和最新诊断
9. 生成风控与分仓建议
10. 生成每日摘要
11. 聚合成首页上下文返回前端

### 8.3 阶段一推荐的数据落地顺序

建议阶段一按以下顺序落地：

1. `daily_info + limit_list_d + kpl_list`
   先完成市场温度和情绪周期
2. `ths_index + ths_daily + ths_member + moneyflow_ind_ths`
   再完成主线题材和板块趋势
3. `daily + daily_basic + moneyflow + stk_limit`
   再完成自选观察和持仓处理
4. `disclosure_date + stk_holdertrade + share_float`
   最后补齐基础风险排雷

如果需要更详细的数据边界和模块映射，应以
[Tushare 6000 积分接口映射](./tushare-6000-interface-map.md) 为准。

### 8.2 触发时机

阶段一建议支持以下触发：

- 首页访问时按需刷新
- 用户手动刷新
- 用户更新持仓后局部刷新

阶段一不强依赖后台定时调度。

## 9. 前端实现建议

### 9.1 首页结构

首页建议分为以下区域：

- 顶部：市场总览 + 情绪周期
- 次级区：主线题材 + 板块趋势 + 今日操作框架
- 中部：今日摘要 + 持仓处理
- 侧栏：自选观察
- 底部或侧边：风控与分仓
- 下部：聊天与 Agent 入口

### 9.2 视觉层级

优先级建议如下：

1. 市场和情绪周期
2. 主线题材、板块趋势和操作框架
3. 持仓和自选
4. 风控与分仓
5. 聊天输入区
6. 通用能力卡片

### 9.3 文案要求

必须替换掉研发说明式文案，例如：

- 阶段性实现说明
- 面向开发者的内部备注

改成面向投资者的正式产品表达。

## 10. 复用与改造策略

### 10.1 可以直接复用

- 持仓 CRUD
- 持仓诊断存储
- 每日摘要存储
- watchlist 数据能力
- 首页路由和主要布局
- 短周期数据接入层原子接口
- 市场脉冲、情绪周期、题材聚焦后端服务原型

### 10.2 需要改造

- 首页第一屏结构
- 自选区视觉和语义
- 持仓建议文案
- 摘要卡和动作卡的排序
- 预期差和可交易性标签
- 当前规则化阈值与字段口径仍需继续清洗和校准

其中截至当前已完成：

- 首页第一屏结构
- 自选区视觉和语义第一版
- 聊天区优先级下调

当前仍待继续完成：

- 预期差和可交易性标签细化
- 自选观察独立服务化
- 持仓动作与风控建议独立服务化

### 10.3 暂时不做

- 新的复杂数据库体系
- 完整题材评分系统
- 复杂策略配置页

## 11. 测试建议

阶段一至少应覆盖：

- 首页上下文组装测试
- 情绪周期阶段识别和轨迹测试
- 持仓建议结构化结果测试
- 自选观察状态生成测试
- 可交易性提示生成测试
- 风控与分仓建议测试
- 前端首页关键组件渲染测试

如果资源有限，至少应保证：

- 首页能稳定展示主要模块
- 持仓和摘要链路不被改坏
- 新增上下文服务有基础单测

## 12. 实施顺序建议

1. 先定义首页上下文对象
2. 再组织市场温度和情绪周期数据
3. 再组织题材和板块趋势
4. 再补风控与分仓建议
5. 再改造首页结构和文案
6. 再增强自选观察区
7. 最后做联调和测试

## 13. 阶段完成标志

当系统能够：

- 在首页第一屏展示市场温度
- 展示情绪周期当前阶段和历史轨迹
- 展示 1 到 3 个重点方向
- 展示基础风控与分仓建议
- 把自选区做成观察池
- 对持仓输出短周期动作建议
- 让聊天区成为次要入口

即可认为阶段一核心目标达成。
