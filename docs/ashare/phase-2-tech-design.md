# 阶段二技术方案

## 1. 目标

在阶段一的短周期工作台之上，建立：

`题材监控 -> 机会池形成 -> 买点裁决 -> 主动提醒`

的完整闭环。

阶段二的重点不在于“模型一直盯全市场”，而在于：

- 先用低成本规则发现方向和候选
- 再用 Agent 对高价值候选做裁决
- 最终把结论变成用户可执行的买点建议

这里的“高价值候选”不只是最强股票，还包括：

- 仍有预期差的股票
- 有持续性但尚未完全一致化的股票
- 当前仍有可交易性的股票
- 主线中的中军龙头和强趋势核心票

## 2. 总体思路

阶段二采用双层结构：

- `规则层`
  负责监控政策、题材、资金和自选池，发现候选
- `裁决层`
  负责判断题材地位、个股位置、预期差、可交易性和买点质量，输出最终建议

这样可以避免“大模型全市场轮询”的高成本方案。

## 2.1 当前前置进度

在进入完整阶段二机会池 MVP 之前，当前仓库已先完成两块可复用前置服务：

- `WatchlistObservationService`
  - 负责把自选股转换为稳定的观察项结构
  - 输出 `items` 与 `all_items`
  - 供首页与后续机会池候选入口复用
- `ThemeCandidateService`
  - 负责把题材方向转换为候选结构
  - 保留 ST / 疑似 ST 不建议参与、创业板/科创板谨慎参与、ETF 不伪造具体代码和名称的规则
- `OpportunityPoolService`
  - 负责把题材候选与自选观察汇总成轻量候选列表
  - 当前仅提供阶段二第一刀的机会池 MVP 后端接口
  - 不包含持久化、提醒中心、生命周期流转、Agent 裁决或自动交易

同时：

- `HomepageContextService` 应保持聚合层定位，不再承载观察规则和题材候选规则
- `EmotionCycleService` 已支持优先复用 window item data 构造时间线，减少逐日重复请求

这意味着当前状态是“阶段二前置服务化 + 机会池 MVP 后端第一刀已完成”，而不是“阶段二完整机会池已经完成”。

## 3. 数据来源建议

阶段二需要把数据优先级重新对齐到短周期语境。

当前阶段二仍默认建立在：

- `Tushare 6000 积分`
- `个人使用`
- `非商业化`
- `不购买独立权限`

之上。

因此阶段二实现时，应优先使用
[Tushare 6000 积分接口映射](./tushare-6000-interface-map.md)，不要默认依赖
8000 积分接口、实时分钟或新闻政策库。

### 3.1 优先数据

- A 股价格和历史行情
- 自选池和持仓池
- 政策和新闻摘要
- 资金流数据
- 涨跌停与强弱数据
- 业绩、减持、解禁等风险事件

### 3.2 推荐接入的 Tushare 接口

阶段二优先建议使用以下接口增强当前系统：

#### 3.2.1 题材扫描和方向归纳

- `ths_index`
- `ths_daily`
- `ths_member`
- `moneyflow_ind_ths`
- `moneyflow_ind_dc`
- `kpl_list`
- `ths_hot`
- `tdx_index`

用途：

- 识别主线和次主线
- 判断题材状态和强弱趋势
- 识别题材代表股和核心承载标的

#### 3.2.2 机会池和买点排序

- `daily`
- `daily_basic`
- `moneyflow`
- `stk_limit`
- `limit_list_d`
- `kpl_list`
- `top_list`
- `top_inst`

用途：

- 判断个股位置、趋势质量和可交易性
- 给机会池排序
- 增强中军龙头和强趋势核心票识别

#### 3.2.3 风险事件与排雷

- `forecast_vip`
- `express_vip`
- `disclosure_date`
- `stk_holdertrade`
- `share_float`

用途：

- 过滤短周期内高概率风险事件
- 给持仓和机会池增加风险修正

阶段二不要求一次性全部接入，但至少应按以上三组优先级规划落地。

### 3.3 模块到接口的建议映射

#### 3.3.1 `topic_scanner_service.py`

建议主接口：

- `ths_index`
- `ths_daily`
- `ths_member`
- `moneyflow_ind_ths`
- `moneyflow_ind_dc`
- `kpl_list`
- `ths_hot`
- `tdx_index`

#### 3.3.2 `opportunity_pool_service.py`

建议主接口：

- `daily`
- `daily_basic`
- `moneyflow`
- `stk_limit`
- `limit_list_d`
- `kpl_list`
- `top_list`
- `top_inst`
- `ths_member`

#### 3.3.3 `entry_timing_service.py`

建议主接口：

- `daily`
- `daily_basic`
- `moneyflow`
- `stk_limit`
- `limit_list_d`
- `kpl_list`

#### 3.3.4 `risk_event_monitor_service.py`

建议主接口：

- `forecast_vip`
- `express_vip`
- `disclosure_date`
- `stk_holdertrade`
- `share_float`

#### 3.3.5 `decision_alert_service.py`

说明：

- 本服务不需要直接请求 Tushare
- 应依赖 `topic_scanner_service.py`、`opportunity_pool_service.py`、
  `entry_timing_service.py` 和 `risk_event_monitor_service.py` 的结果

## 4. 领域模型建议

### 4.1 `topic_profile`

用于表示当前被系统识别的方向或题材。

建议字段：

- `id`
- `trading_date`
- `topic_name`
- `topic_state`
- `summary`
- `signal_score`
- `source_events_json`
- `representative_tickers_json`

### 4.2 `opportunity_candidate`

用于表示进入机会池的股票。

建议字段：

- `id`
- `user_id`
- `ticker`
- `topic_name`
- `candidate_state`
- `priority_score`
- `expectation_gap_score`
- `continuity_score`
- `tradeability_state`
- `role_label`
- `trend_quality`
- `ranking_bucket`
- `reasons_json`
- `time_horizon`
- `created_at`
- `updated_at`

### 4.3 `entry_signal`

用于保存某次买点判断结果。

建议字段：

- `id`
- `candidate_id`
- `action`
- `confidence`
- `summary`
- `reasons_json`
- `tradeability_state`
- `expectation_gap_view`
- `missing_confirmations_json`
- `invalid_conditions_json`
- `created_at`

### 4.4 `decision_alert`

用于主动提醒。

建议字段：

- `id`
- `user_id`
- `ticker`
- `topic_name`
- `alert_type`
- `priority`
- `title`
- `body`
- `payload_json`
- `created_at`
- `read_at`

## 5. 策略和偏好的表示方式

阶段二不建议一开始做复杂 DSL，而是采用：

`模板 + 自然语言补充 + 结构化配置`

### 5.1 推荐模板

- 政策催化
- 事件驱动
- 趋势延续
- 回调后二次走强
- 低位启动

### 5.2 可解析字段

系统可将用户输入解析为：

- 偏好题材
- 偏好持有周期
- 偏好进攻或稳健
- 不接受的风险类型
- 买入风格偏好
- 是否接受高位追强
- 是否更偏好预期差型机会
- 是否更偏好龙头 / 中军而非小票跟风

## 6. 扫描引擎

### 6.1 规则扫描职责

规则层负责：

- 监控题材和方向变化
- 扫描自选池和候选池
- 发现进入观察状态的股票
- 控制唤醒成本
- 过滤掉明显没有可交易性的伪机会
- 优先把核心票放到前排，把弱票降权

### 6.2 规则扫描输入

- 用户偏好和模板
- 价格、成交量、历史行情
- 政策和新闻摘要
- 资金流与涨跌停数据
- 风险事件数据

### 6.3 规则扫描输出

- 方向观察对象
- 股票候选对象
- 初步优先级
- 初步触发原因
- 预期差标签
- 可交易性标签
- 角色标签
- 趋势质量标签

## 7. Agent 裁决层

### 7.1 建议新增 Agent

- `PolicyNewsAgent`
- `ThemeHeatAgent`
- `LeaderRankingAgent`
- `ExpectationGapAgent`
- `TradeabilityAgent`
- `EntryTimingAgent`
- `OpportunityJudgeAgent`

### 7.2 职责拆分

#### PolicyNewsAgent

- 判断政策或事件是否具备持续性
- 识别短周期方向催化

#### ThemeHeatAgent

- 判断题材是加强、扩散、分歧还是退潮

#### LeaderRankingAgent

- 判断题材内谁更像核心票、中军票或跟风票
- 判断哪些票更像“能吃到主升”的核心承载标的

#### ExpectationGapAgent

- 判断当前催化是否还有未充分定价的空间
- 判断当前是一致性强化，还是仍存在预期差

#### TradeabilityAgent

- 判断当前是否还可以买
- 判断涨跌停或流动性风险是否让机会只适合持有而不适合新增

#### EntryTimingAgent

- 判断现在是继续观察、等待确认还是进入买点窗口

#### OpportunityJudgeAgent

- 汇总各类结论
- 输出最终机会卡片和提醒内容

## 8. 输出协议

阶段二的输出必须优先结构化，而不是长篇自由文本。

### 8.1 机会卡

至少应包含：

- `action`
- `topic_name`
- `priority_score`
- `expectation_gap_level`
- `continuity_level`
- `tradeability_state`
- `role_label`
- `trend_quality`
- `summary`
- `reasons`
- `time_horizon`
- `missing_confirmations`
- `invalid_conditions`

### 8.2 提醒卡

至少应包含：

- `alert_type`
- `priority`
- `title`
- `body`
- `next_action`

## 9. 调度设计

### 9.1 触发方式

阶段二建议支持：

- 周期扫描
- 关键事件触发
- 用户主动刷新

### 9.2 扫描频率

初期建议分钟级以上，不追求毫秒级。

### 9.3 去重机制

需要对以下对象去重：

- 同一方向重复升温提醒
- 同一股票重复买点提醒
- 已失效但未更新状态的旧候选

## 10. 前端设计建议

### 10.1 新增页面

- 题材雷达页
- 机会池页
- 偏好与模板页
- 提醒中心

### 10.2 首页联动

阶段二需要把最重要的机会池内容回流到首页，例如：

- 今日新进入重点观察的方向
- 今日最高优先级机会
- 今日仅适合持有、不宜追买的强票
- 今日弱票降权提示
- 重点提醒摘要

## 11. 成本与性能控制

### 11.1 控制原则

- 先规则层粗筛
- Agent 只处理高价值候选
- 限制同一用户每日裁决次数
- 避免把“已经买不进去”的结果全部当成有效机会频繁推送
- 避免让半死不活的弱票占用过多候选位

### 11.2 限流建议

- 单用户模板数量上限
- 单日机会池上限
- 同一只股票单日重复分析上限

## 12. 测试建议

阶段二至少应覆盖：

- 题材监控结果基本测试
- 机会池生成测试
- 买点建议结构测试
- 提醒去重测试
- 预期差与可交易性标签测试
- 核心票优先级排序测试
- 关键 Agent 的冒烟测试

## 13. 实施顺序建议

1. 先实现题材和方向对象
2. 再实现机会池和候选生命周期
3. 再接买点裁决
4. 最后接提醒中心
