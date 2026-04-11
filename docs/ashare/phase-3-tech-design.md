# 阶段三技术方案

## 1. 目标

建立 ValueCell 的短周期 A 股裁决中台，让系统具备基于统一信息链和统一时间窗的：

- 持仓生命周期判断
- 卖点裁决
- 冲突信号解释
- 历史复盘

阶段三最重要的技术变化，不是“多几个 Agent”，而是增加一个稳定的：

`短周期决策上下文构建层`

让 Agent 看到的不是碎片数据，而是已经按时间、题材、标的和方向整理过的上下文。

## 2. 设计原则

### 2.1 不做数据堆砌

重点不是给模型更多原始字段，而是让多层数据可比较、可排序、可解释。

### 2.2 不做规则爆炸

面对政策利好、题材退潮、资金撤离、个股破位这种混合情况，避免写成大量
if/else 组合。

### 2.3 先服务“什么时候卖”

阶段三的数据和 Agent 设计要优先回答：

- 还能不能拿
- 是否该先减仓
- 是否已经进入退出窗口

### 2.4 先判断预期是否证伪，再判断怎么退出

阶段三不能把“卖点”理解为单一价格触发器。

更合理的顺序是：

1. 预期是否仍在
2. 持续性是否还在
3. 当前是否有可交易性
4. 它是不是中军龙头或强趋势核心票
5. 再决定继续持有、减仓、等待修复还是退出

### 2.5 人可读、机可裁决

所有中间结果既要能被程序消费，也要能被用户理解和复盘。

## 3. 核心架构

阶段三新增一个核心中间层：

`ShortCycle Decision Engine`

它位于数据接入层和最终 Agent 输出之间。

### 3.1 新分层

#### 数据接入层

- 行情和成交数据
- 政策和新闻数据
- 题材和热度数据
- 资金流和龙虎榜数据
- 风险事件数据

#### 事件归一层

将不同来源的数据归一为统一短周期事件对象。

#### 时间窗上下文层

将统一事件按：

- ticker
- topic
- 时间窗口
- 方向
- 可交易性状态

整理为决策上下文。

#### 裁决层

各类 Agent 从不同角度审阅上下文，再由总裁决 Agent 给出动作建议。

#### 复盘层

记录关键建议与结果，用于后续评估。

## 4. 统一事件模型

建议新增统一事件对象 `ShortCycleContextEvent`。

建议字段：

- `event_id`
- `ticker`
- `topic_name`
- `layer`
- `event_type`
- `source`
- `occurred_at`
- `ingested_at`
- `importance_score`
- `direction`
- `time_horizon`
- `tradeability_hint`
- `summary`
- `payload_json`

字段说明：

- `layer`：对应短周期信息链层级
- `direction`：偏多 / 偏空 / 中性 / 风险 / 确认
- `time_horizon`：5 / 10 / 20 / 40 个交易日等

## 5. 时间窗上下文模型

建议新增 `DecisionContextWindow`：

- `window_id`
- `ticker`
- `topic_name`
- `window_start`
- `window_end`
- `market_state`
- `support_events_json`
- `opposing_events_json`
- `risk_events_json`
- `position_state`
- `expectation_state`
- `tradeability_state`
- `exit_liquidity_plan`
- `role_label`
- `trend_quality`
- `summary`

### 5.1 时间窗层的作用

时间窗层主要解决两个问题：

- 同一只股票的信号并不是同一时间出现
- 短周期用户最关心的是未来 1 到 4 周，而不是无限长时间轴

因此阶段三要把“最近几天到几周内的时间差”变成显式可读内容。

## 6. Agent 拆分建议

### 6.1 建议拆分的 Agent

- `MarketRegimeAgent`
- `PolicyEventAgent`
- `ThemeRhythmAgent`
- `CapitalBehaviorAgent`
- `StockPositionAgent`
- `ExpectationGapAgent`
- `TradeabilityRiskAgent`
- `ExitJudgeAgent`
- `DecisionJudgeAgent`
- `ReviewAgent`

### 6.2 职责说明

#### MarketRegimeAgent

- 判断市场环境是否支持继续持有或继续进攻

#### PolicyEventAgent

- 判断政策和事件是否仍在支撑当前逻辑

#### ThemeRhythmAgent

- 判断题材是在加强、分歧还是退潮

#### CapitalBehaviorAgent

- 判断资金是在承接、观望还是撤离

#### StockPositionAgent

- 判断个股是否仍处在健康位置
- 判断它是中军龙头、强趋势核心，还是边缘弱票

#### ExpectationGapAgent

- 判断当前预期是在延续、兑现还是证伪

#### TradeabilityRiskAgent

- 判断涨跌停、流动性和退出难度
- 为“卖不卖得出”提供上下文

#### ExitJudgeAgent

- 直接服务卖点和减仓建议
- 对核心票和弱票给出不同的容错与退出节奏

#### DecisionJudgeAgent

- 汇总上面结果，生成最终动作卡

#### ReviewAgent

- 对历史建议做复盘和有效性总结

## 7. 决策协议

建议所有子 Agent 输出统一协议：

- `thesis`
- `support_points`
- `opposing_points`
- `risk_flags`
- `confidence`
- `time_horizon`
- `action_bias`
- `expectation_view`
- `tradeability_view`
- `role_view`

总裁决 Agent 再统一生成最终卡片：

- 动作
- 当前持仓阶段
- 核心假设
- 支持证据
- 反对证据
- 风险等级
- 观察窗口
- 失效条件
- 可交易性状态
- 退出执行建议
- 核心票身份说明

## 8. 数据存储建议

建议新增：

- `short_cycle_context_event`
- `decision_context_window`
- `holding_lifecycle_state`
- `decision_record`
- `decision_outcome_review`

如果实现成本过高，可先将部分对象做为缓存或快照，不强制一开始全部完整落库。

## 9. 数据源增强建议

阶段三建议重点增强以下数据：

- `moneyflow`
- `top_list`
- `forecast`
- `express`
- `disclosure_date`
- `stk_holdertrade`
- `share_float`
- 更多政策和新闻源

原因是阶段三需要更强的：

- 资金节奏
- 事件时间窗
- 风险触发
- 卖点解释
- 流动性和涨跌停边界判断

## 10. 调度与计算链路

### 10.1 事件入库

所有外部数据先转换为统一事件对象。

### 10.2 上下文构建

按 ticker、topic 和时间窗构建上下文快照。

### 10.3 裁决触发

以下情况触发裁决：

- 阶段二机会池进入关键窗口
- 持仓风险升级
- 用户主动请求分析
- 重要事件触发

### 10.4 复盘生成

在后续时间点记录结果，形成建议与结果的闭环。

## 11. 实施顺序建议

阶段三建议按以下顺序推进：

1. 先做统一事件模型
2. 再做时间窗上下文
3. 再做持仓生命周期状态
4. 再做卖点裁决
5. 最后接复盘闭环

## 12. 测试与验证重点

阶段三不应只测试“代码能跑”，还应关注：

- 统一事件是否正确归类
- 时间窗是否保留关键先后关系
- 冲突信号是否被正确区分
- 卖点建议是否可解释
- 复盘记录是否可追溯
- 跌停或接近跌停时的退出建议是否合理
- 核心票和弱票是否被正确区分处理

## 13. 阶段完成标志

当系统能够：

- 将多层信号放进统一时间窗
- 给出结构化卖点建议
- 在矛盾信号中解释为什么这样处理
- 对历史建议进行可回放复盘
- 能区分“预期未证伪的扛波动”和“预期证伪后的退出”

即可认为阶段三核心能力建立完成。
