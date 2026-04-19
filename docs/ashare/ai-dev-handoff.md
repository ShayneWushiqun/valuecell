# A 股短周期投资助手 AI 开发交接说明

## 1. 文档目的

本文件用于把 `docs/ashare/` 下的阶段文档交给另一个 AI 编码工具执行。

目标是让它理解：

- 当前项目不再优先做长期价值研究工具
- 当前项目要服务的是 `1 到 2 个月周期` 的 A 股投资者
- 每一阶段该先做什么
- 哪些东西不能擅自扩张
- 每轮交付应达到什么标准

## 2. 当前产品方向

当前新的产品方向是：

`一个围绕预期差、持续性、可交易性、政策、题材、情绪、资金和持仓处理工作的 A 股短周期决策系统。`

默认偏好应进一步明确为：

- 优先青睐主线中的中军龙头和强趋势核心票
- 明确降权半死不活、边缘跟风、热度不足的弱票

但首页信息顺序仍应先全局、后个股：

1. 市场总览
2. 情绪周期阶段与轨迹
3. 主流题材和板块趋势
4. 个股观察和机会
5. 持仓处理
6. 风控与分仓

核心问题不是“哪个公司三年后最好”，而是：

- 现在市场能不能做
- 哪个题材正在形成主线
- 哪只票更值得进入机会池
- 现在是不是合适买点
- 现在买不买得进去，错了卖不卖得出来
- 当前持仓要不要继续拿
- 什么情况下应该卖出

## 3. 重要原则

### 3.1 优先做完整闭环，不优先做大而全

不要一开始同时实现阶段一、阶段二、阶段三。

应先完成阶段一最小闭环，再逐步推进。

### 3.2 优先复用现有结构，但允许重构产品语义

应优先复用仓库里已有的：

- `valuecell.server` 的 API 和 service 模式
- `valuecell.server.db` 的 model/repository 模式
- `valuecell.adapters.assets` 的 A 股数据能力
- `valuecell.core` 的任务和 Agent 编排能力
- `frontend/src/app/home` 的首页与股票相关页面

但允许对现有“持仓中心”实现重新定义产品语义，使其服务短周期目标。

### 3.3 不要擅自把项目做成价值研究系统

以下方向在没有明确指令时不要提前加重：

- 长篇财报解读
- 长期估值体系
- 以基本面为唯一主轴的研究页
- 超出 1 到 2 个月窗口的长期配置逻辑

### 3.4 不要在没有明确需求时扩大范围

以下方向在没有明确指令时不要提前实现：

- 自动交易
- 高复杂度 DSL
- 高频实时扫盘
- 多市场支持
- 大量外部依赖接入

### 3.5 所有输出都必须可执行

所有输出都应尽量围绕结构化建议卡，而不是长篇泛泛分析。

最少应包含：

- 动作
- 核心理由
- 预期差或预期证伪判断
- 可交易性判断
- 题材地位判断：龙头 / 中军 / 跟风 / 弱势
- 当前适用周期
- 风险等级
- 触发条件
- 失效条件

### 3.6 不要把涨得高和跌得多当成简单结论

另一个 AI 工具实现时，不能默认：

- 高位票一定该卖
- 低位票一定安全
- 跌停就一定立即清仓
- 涨停就一定值得追

更合理的判断顺序应是：

1. 预期差是否仍在
2. 逻辑是否仍有持续性
3. 当前是否还有可交易性
4. 它是不是中军龙头或强趋势核心票
5. 再决定买、持有、减仓或卖出

## 4. 阅读顺序

1. 先读 [README](./README.md)
2. 再读 [Tushare 6000 积分接口映射](./tushare-6000-interface-map.md)
3. 再读 [阶段一需求文档](./phase-1-prd.md)
4. 再读 [阶段一技术方案](./phase-1-tech-design.md)
5. 如果阶段一开发完成，再进入阶段二
6. 阶段三只作为后续目标，不得在阶段一中提前过度设计
7. 阶段四应在阶段二和阶段三已有结构化能力基础上推进，不得在阶段一混入线程式研究工作区

## 5. 当前默认数据边界

当前文档默认：

- 个人使用
- 非商业化
- 数据主源为 `Tushare 6000 积分`
- 不默认购买新闻、公告、政策、研报、实时分钟等独立权限

因此另一个 AI 编码工具在实现时：

- 应优先使用 [Tushare 6000 积分接口映射](./tushare-6000-interface-map.md)
  中列出的接口
- 不应直接假设 8000 积分接口可用
- 不应直接假设新闻、公告、政策库已经可用
- 如果某个能力必须依赖独立权限，必须先在文档中明确标注

## 6. 当前默认开发目标

如果没有额外说明，默认当前开发目标是：

`仅实现阶段一：短周期首页与观察台`

阶段一要形成一个可运行的最小闭环：

- 首页能展示今日市场温度
- 首页能展示情绪周期当前阶段和最近一段时间走向
- 首页能展示主线题材或重点方向
- 首页能展示哪些机会仍有预期差，哪些只适合观察
- 首页能展示自选观察和持仓处理建议
- 首页能给出基础风控和分仓建议
- 用户能快速知道“今天先看什么”
- 用户能看出哪些票值得优先盯，因为它们是核心票

## 6.1 当前已落地的后端短周期基础

当前仓库已经不是“完全从零开始”的状态，下面这些短周期后端基础已存在：

- `python/valuecell/adapters/assets/tushare_adapter.py`
  - 已新增阶段一和阶段二优先接口的统一访问方法
- `python/valuecell/adapters/assets/tushare_short_cycle_gateway.py`
  - 已提供市场脉冲、题材聚焦、个股观察三类 bundle 入口
- `python/valuecell/server/services/assets/short_cycle_data_service.py`
  - 已提供结构化数据输出层
- `python/valuecell/server/services/assets/market_pulse_service.py`
  - 已提供市场状态、动作建议和信号摘要
- `python/valuecell/server/services/assets/emotion_cycle_service.py`
  - 已提供情绪阶段和时间轨迹
- `python/valuecell/server/services/assets/theme_focus_service.py`
  - 已提供题材聚焦、代表票、核心票和预期差等级
- `python/valuecell/server/services/assets/watchlist_observation_service.py`
  - 已把首页自选观察规则抽成可复用服务，输出首页重点观察和完整观察列表
- `python/valuecell/server/services/assets/theme_candidate_service.py`
  - 已把题材候选结构化规则抽成独立服务，供首页与后续机会池复用
- `python/valuecell/server/services/assets/opportunity_pool_service.py`
  - 已提供机会池 MVP 后端候选聚合，基于自选观察与题材候选生成稳定排序列表
- `python/valuecell/server/services/assets/entry_timing_service.py`
  - 已提供规则版买点裁决信号，基于机会池候选输出保守 action 和确认项
- `python/valuecell/server/services/assets/decision_alert_service.py`
  - 已提供轻量提醒摘要，基于买点裁决信号输出买点接近、等待确认、持有观察和风险回避
- `frontend/src/app/home/opportunities.tsx`
  - 已提供阶段二机会池页面，集中展示候选机会、买点裁决和今日提醒摘要
- `python/valuecell/server/services/assets/strategy_preference_service.py`
  - 已提供 A 股策略偏好模板 MVP，复用 user_profiles 存储并影响机会池排序、买点裁决和提醒优先级
- `python/valuecell/server/services/assets/decision_alert_persistence_service.py`
  - 已提供提醒中心持久化 MVP，支持刷新、列表、已读、全部已读和忽略
- `python/valuecell/server/services/assets/ashare_decision_context_service.py`
  - 已提供单 ticker 的 Agent 裁决上下文 MVP，统一组合市场、题材、候选、买点信号、提醒、偏好与持仓摘要
- `python/valuecell/server/services/assets/ashare_decision_judge_service.py`
  - 已提供 Agent 裁决接口 MVP，默认只走规则 fallback，输出结构化 judgement
- `python/valuecell/server/services/portfolio/holding_exit_signal_service.py`
  - 已提供持仓卖点与减仓裁决 MVP，区分继续持有、持有观察、减仓观察、保护利润和纪律止损
- `python/valuecell/server/services/assets/ashare_daily_workbench_service.py`
  - 已提供 A 股每日决策总控台 MVP，负责把市场、机会、提醒和持仓处理聚合到一个编排层
- `python/valuecell/server/services/assets/ashare_daily_snapshot_service.py`
  - 已提供每日快照与复盘中心 MVP 的快照沉淀能力，按日记录总控台编排结果
- `python/valuecell/server/services/assets/theme_radar_service.py`
  - 已提供题材雷达中心 MVP，聚合题材状态、参与边界、偏好命中与观察/机会共振
- `python/valuecell/server/services/assets/watchlist_center_service.py`
  - 已提供观察池中心 MVP，聚合自选观察、提醒联动、机会池联动与持仓关系
- `python/valuecell/server/services/assets/holding_lifecycle_service.py`
  - 已提供持仓周期中心 MVP，给每只持仓归类为固定生命周期阶段并补处理框架
- `python/valuecell/server/services/assets/exit_risk_center_service.py`
  - 已提供卖点与风险中心 MVP，按优先级集中展示保护利润、纪律止损与观察项
- `python/valuecell/server/services/assets/decision_record_service.py`
  - 已提供决策记录沉淀 MVP，按日记录关键持仓处理建议，供复盘中心回看
- `python/valuecell/server/services/assets/short_cycle_context_event_service.py`
  - 已提供统一事件模型 MVP，围绕重点标的宇宙归一市场、题材、机会、提醒与持仓判断
- `python/valuecell/server/services/assets/decision_context_window_service.py`
  - 已提供决策时间窗上下文 MVP，把最近 10 / 20 / 40 日的支持、反对和风险证据整理为可读窗口
- `frontend/src/app/home/daily-workbench.tsx`
  - 已提供每日决策总控台页面，用于每日先看风险、持仓和机会摘要
- `frontend/src/app/home/daily-review.tsx`
  - 已提供复盘中心页面，用于回看和比较最近几天的 snapshot 变化
- `frontend/src/app/home/theme-radar.tsx`
  - 已提供题材雷达页面，用于集中查看方向强弱、参与边界和题材共振
- `frontend/src/app/home/watchlist-center.tsx`
  - 已提供观察池中心页面，用于集中查看重点观察、自选联动和持仓关系
- `frontend/src/app/home/holding-lifecycle.tsx`
  - 已提供持仓周期中心页面，用于查看所有持仓当前所处阶段与处理框架
- `frontend/src/app/home/exit-risk-center.tsx`
  - 已提供卖点与风险中心页面，用于集中处理高优先级持仓风险
- `frontend/src/app/home/decision-contexts.tsx`
  - 已提供决策上下文页，用于系统查看某只票最近时间窗的支持、反对与风险链条
- `frontend/src/app/home/alerts.tsx`
  - 已提供提醒中心页面，可回看提醒并执行已读 / 忽略
- `frontend/src/app/home/strategy-preferences.tsx`
  - 已提供策略偏好配置页，可选择模板并保存风格参数
- `frontend/src/app/home/components/ashare-decision-context-dialog.tsx`
  - 已提供机会池候选卡上的裁决上下文轻量弹窗入口
- `docs/ashare/phase-4-prd.md`
  - 已定义股票分析聊天工作区、线程式研究、多上下文卡片和多入口进入方式
- `docs/ashare/phase-4-tech-design.md`
  - 已定义阶段四的线程模型、上下文卡片协议、工作区编排层和工具分层策略

但要注意：

- 上述能力当前主要是结构化服务层 + 工作台页面
- 现在已经补上首页上下文聚合服务、首页工作台第一屏，以及股票分析研究线程工作区
- 阶段四第一轮已完成工作区骨架、研究线程 CRUD、上下文卡片 CRUD 和 TradingAgents 接入口
- 阶段四第二轮已完成多模块 context import、context assembler、研究线程消息历史与 `context_only` 聊天 MVP
- 阶段四第三轮已完成 `StockAnalysisToolPlanner`、按需补数模式、临时证据补充区和高级研究卡片接入
- 阶段四第四轮已完成第三层外部解释型补数第一版、临时证据保存为长期上下文、证据来源与时效说明
- 阶段四第五轮已完成显式对比研究、线程分叉增强、上下文刷新与时效治理
- 阶段四第六轮已完成批量 stale refresh、刷新后重答工作流、refresh diff 摘要、研究流摘要区和外部 provider 编排收口
- 阶段四核心 MVP 已完成，阶段五第一轮-A 已完成显式线程研究记忆 MVP，第一轮-B 已完成 context compression，第二轮已完成 question routing 与 research tasks，第三轮已完成 execution planning / task-driven research / validation summary / execution trace
- 当前仍未接自动长期记忆系统、自动交易、更强 multi-step autonomous planning 和更复杂的 SSE 工具可视化

## 6.2 当前阶段推进建议

如果当前开发已经完成阶段三的大部分结构化闭环，后续优先级建议调整为：

1. 先继续增强阶段三的结果回看、有效性和风控分仓能力
2. 再在阶段四现有 context_only 工作区上继续补外部工具层和研究卡片类型
3. 阶段四要优先复用：
   - `conversation`
   - `agent_stream`
   - `TradingAgents`
   - `持仓 / 机会池 / 观察池 / 题材雷达 / 提醒 / 决策上下文`
4. 阶段四不要直接变成“到处塞聊天框”，而应继续统一收敛为线程式研究工作区

## 6.3 阶段四当前实现状态

当前代码已经具备：

- `stock_analysis_thread` 与 `analysis_context_card` 两个核心模型
- `StockAnalysisWorkspaceService` 统一管理线程 CRUD、卡片 CRUD 和多模块 context import
- `StockAnalysisContextAssembler` 负责把当前线程卡片装配成稳定 prompt context
- `StockAnalysisToolPlanner` 负责判定 `context_only / need_tooling / user_forced_tooling`
- `StockAnalysisToolingService` 负责补内部结构化结果、日线行情和临时证据块
- `StockAnalysisExternalToolService` 负责第三层外部新闻与外部确认补数，并在不可用时优雅降级
- `StockAnalysisMessageService` 负责按 `thread.conversation_id` 读取历史、写入消息并执行默认回答或按需补数回答
- `POST /api/v1/stock-analysis/threads/{thread_id}/messages/{message_id}/save-evidence`
  - 已可把 assistant 某条临时证据显式保存为长期上下文卡片
- `/api/v1/stock-analysis/threads/{thread_id}/messages`
  - 已可在同一线程中多轮继续聊，并返回 `mode / answer_basis / tool_reason / temporary_evidence_blocks`
- `/api/v1/stock-analysis/threads/{thread_id}/compare-targets`
  - 已可显式读取和维护 compare targets，稳定返回来源、主次角色、排序和比较对象列表
- `/api/v1/stock-analysis/threads/{thread_id}/fork`
  - 已可基于所选上下文卡片和 compare targets 分叉出新线程，且不复制旧消息历史
- `/api/v1/stock-analysis/threads/{thread_id}/contexts/{context_id}/refresh`
  - 已可对可定位 source_ref 的上下文卡片复用现有 builder 做单卡刷新
- `/api/v1/stock-analysis/threads/{thread_id}/contexts/refresh-stale`
  - 已可批量刷新 stale / refresh_recommended 的上下文卡片，并返回结构化 diff 摘要
- `/api/v1/stock-analysis/threads/{thread_id}/memories`
  - 已可显式列出线程研究记忆、当前 active memory 和历史版本摘要
- `/api/v1/stock-analysis/threads/{thread_id}/memories/capture`
  - 已可基于显式上下文、compare targets、最近关键问答、refresh / evidence 摘要生成新的研究记忆快照
- `/api/v1/stock-analysis/threads/{thread_id}/memories/{memory_id}/activate`
  - 已可把某个历史研究记忆切为当前 active memory，且保持线程内唯一 active
- `/api/v1/stock-analysis/threads/{thread_id}/memories/{memory_id}/refresh`
  - 已可基于旧记忆和当前线程状态生成新版记忆，并自动切为 active
- `/api/v1/stock-analysis/threads/{thread_id}/compressions`
  - 已可显式列出线程对话压缩、当前 active compression、压缩建议和未压缩消息统计
- `/api/v1/stock-analysis/threads/{thread_id}/compressions/capture`
  - 已可基于最近消息、compare targets、refresh / tooling / evidence 摘要与 active memory 生成新的对话压缩摘要
- `/api/v1/stock-analysis/threads/{thread_id}/compressions/{compression_id}/activate`
  - 已可把某个历史 compression 切为当前 active compression，且保持线程内唯一 active
- `/api/v1/stock-analysis/threads/{thread_id}/compressions/{compression_id}/refresh`
  - 已可基于旧 compression 和当前线程状态生成新版压缩摘要，并自动切为 active
- `/api/v1/stock-analysis/threads/{thread_id}/research-tasks`
  - 已可显式列出线程 research tasks，并返回 open/high priority 统计、最近 generate 时间和 actionable gap 摘要
- `/api/v1/stock-analysis/threads/{thread_id}/research-tasks/generate`
  - 已可从 active memory、active compression、compare targets、refresh 状态和 assistant routing metadata 中显式生成研究任务
- `/api/v1/stock-analysis/threads/{thread_id}/research-tasks/{task_id}/complete|reopen|dismiss`
  - 已可把研究任务显式完成、重开或忽略，不做后台自动调度
- `/api/v1/stock-analysis/threads/{thread_id}/messages`
  - 已支持可选 `research_task_id`，并在 assistant metadata 中返回 execution plan、executed/skipped/failed steps、validation summary、task update suggestions、focus tickers/themes
- `/home/stock-analysis`
  - 已从骨架页升级为可用聊天工作区，支持“发送”“补数据后再回答”“刷新过期上下文后再回答”“保存为上下文”“compare tray”“分叉线程”“研究流摘要区”“研究记忆面板 / 历史版本 / 激活 / 刷新”“compression panel / 历史版本 / 激活 / 刷新”“research task panel / 生成 / 手动创建 / 完成 / 重开 / 忽略 / 围绕此任务继续研究”“assistant routing explanation”“execution trace / validation / task suggestions”和“上下文刷新”

当前仍需留到下一轮的点：

- 自动长期记忆系统、更细的 planner 语义
- 更复杂的 SSE 工具过程可视化
- 更强的第三层 provider 扩展与更多解释型来源
- 更复杂的研究归因 / 绩效反馈
- 更强的 multi-step autonomous planning
- 已新增 `/api/v1/homepage/context` 作为前端消费入口
- 聊天和通用 Agent 已降级到页面次要区域
- `HomepageContextService` 当前应只做聚合，不再承载自选观察和题材候选的具体规则
- `EmotionCycleService` 已支持优先复用 window item data，减少时间线逐日重复请求
- 已完成阶段二 MVP 规则版闭环：机会池、买点裁决、轻量提醒摘要与机会池页面
- 已完成策略偏好模板 MVP，能轻量影响排序与提醒优先级
- 已完成提醒中心持久化 MVP，但还没有完成完整复杂提醒系统
- 已完成 Agent 裁决上下文 MVP，但还没有接真实 LLM 裁决
- 已完成 Agent 裁决接口 MVP，但默认仍是规则 fallback
- 已完成持仓卖点与减仓裁决 MVP，持仓侧处理已与新开仓裁决解耦
- 已完成 A 股每日决策总控台 MVP，形成“市场 -> 机会 -> 提醒 -> 持仓处理”的日常工作流
- 已完成每日快照与复盘中心 MVP，支持日级快照沉淀和最近几天的变化回看
- 已完成题材雷达中心 MVP，补齐方向强弱、参与边界与共振关系的独立页面
- 已完成观察池中心 MVP，补齐自选观察、提醒联动、机会池联动与持仓关系的独立页面
- 已完成持仓周期中心 MVP，补齐“当前持仓处于哪个阶段”的统一视图
- 已完成卖点与风险中心 MVP，补齐“今天优先处理什么持仓”的独立操作台
- 已完成 `DecisionOutcomeReview` 后端 MVP，支持 5 / 10 / 20 日日级轻量结果回看
- 已完成 `DecisionEffectivenessService` MVP，能汇总最近 40 天 review 的有效性摘要
- 已完成 `RiskSizingService` MVP，能独立给出组合层和 ticker 层的保守分仓区间建议
- 已完成 `decision reviews` 与 `risk sizing` 前端页面，并补齐复盘中心、总控台、决策上下文页和机会池的轻量入口联动
- 当前仍未做复杂回测、分钟级复盘、真实 LLM 和自动交易
- 已完成决策记录沉淀 MVP，补齐“当时为什么这么判断”的复盘材料
- 已完成统一事件模型 MVP，围绕重点标的宇宙形成可去重、可解释的短周期事件对象
- 已完成决策时间窗上下文 MVP，支持 10 / 20 / 40 日窗口的支持 / 反对 / 风险证据整理
- 已完成决策上下文页 MVP，补齐“当前为什么这样判断”的独立解释页
- 还没有完成更细粒度提醒去重与历史运营能力和自动交易
- 部分规则仍是轻量版，需要继续校准字段口径和阈值
- 还没有完成分钟级实时事件流、全市场事件总线和复杂收益归因

## 6.2 当前首页收敛进度

当前首页第一屏已经从“欢迎页 + 持仓摘要 + 聊天入口”收敛为更接近阶段一目标的工作台结构：

1. 市场总览
2. 情绪周期与最近轨迹
3. 主流题材和板块趋势
4. 今日操作框架
5. 自选观察
6. 持仓处理
7. 风控与分仓策略

同时需要明确：

- `portfolio-overview.tsx` 的持仓 CRUD 链路仍保留并继续复用
- 自选区已改成观察池表达，但当前仍是轻量规则版
- 首页聚合层 `homepage_context_service.py` 只应做服务聚合，不应退化为新的散乱数据源调用中心

## 7. 对 AI 编码工具的工作要求

### 6.1 每次开发前

需要先输出：

- 它对任务的理解
- 它计划修改哪些文件
- 它打算先实现哪个子目标
- 它明确不做哪些内容

### 6.2 每次开发中

需要遵守：

- 尽量小步提交
- 不修改与当前目标无关的模块
- 不重构大范围代码，除非明确有必要
- 尽量在现有命名和目录风格下实现
- 文案和页面语义必须贴近短周期 A 股场景

### 6.3 每次开发后

需要输出：

- 修改了哪些文件
- 完成了哪些目标
- 哪些点仍是暂未实现或待确认
- 跑了哪些测试或校验

## 8. 阶段一的建议拆分

建议拆成 5 个连续小目标：

### 7.1 小目标一：市场工作台首页

- 首页第一屏以市场温度、情绪周期、主线题材、今日摘要为主
- 聊天区仍可保留，但视觉优先级下降

### 7.2 小目标二：自选观察区

- 自选股不再只是简单列表
- 能体现异动、强弱、重点关注、预期差和观察原因
- 能体现它是龙头、中军还是弱跟风

### 7.3 小目标三：持仓处理区

- 每只持仓都有短周期动作建议
- 明确当前是持有、减仓、卖出还是观察
- 能区分“短期大跌但预期未证伪”和“逻辑开始破坏”
- 对核心票和弱票的容错策略不同

### 7.4 小目标四：日总结与刷新链路

- 用户每天打开首页能看到“今天先看什么”
- 用户可刷新摘要和观察结果

### 7.5 小目标五：风控和分仓建议

- 首页能给出基础总仓位和单票仓位建议
- 能区分试错仓、确认仓和防守仓

## 9. 阶段完成定义

如果 AI 编码工具声称“阶段一完成”，至少应满足：

- 首页看起来像短周期投资工作台，而不是聊天首页
- 用户能看到市场温度或市场状态摘要
- 用户能看到情绪周期阶段和最近一段轨迹
- 用户能看到主线题材或重点关注方向
- 用户能看到基本的预期差和可交易性表达
- 用户能看到自选观察和持仓处理
- 用户能看到基础风控和分仓策略
- 建议卡不是空泛描述，而是有动作和理由
- 用户能看出系统在优先推荐中军龙头，而不是平均推荐所有题材票

## 10. 明确的非目标

当前文档不要求另一个 AI 工具实现以下内容：

- 证明策略必然赚钱
- 复杂高频量化
- 完整事件图谱
- 所有提醒渠道
- 实盘券商连接
- 多市场联动系统

## 11. 风险提醒

另一个 AI 工具很可能会犯以下错误，应主动避免：

- 继续按旧思路把阶段一做成“持仓研究页”
- 过度强调长期基本面和估值
- 一开始就做复杂题材识别系统
- 为了“看起来完整”做大量后台配置页
- 在没有市场语境的情况下直接给个股结论
- 首页一上来就推荐个股，没有先给全局市场环境和情绪周期
- 只因为涨得高就判定风险，或只因为跌得多就判定机会
- 忽略 A 股涨跌停导致的买入和卖出可交易性问题
- 对中军龙头和边缘跟风给出几乎一样的优先级
- 默认调用 8000 积分以上接口，导致实际无法落地
- 默认依赖新闻、公告、政策库等独立权限，导致当前方案超预算

## 12. 推荐交付节奏

建议让另一个 AI 工具按以下方式工作：

1. 先只实现阶段一首页与前端工作台
2. 再补阶段一需要的轻量后端数据组织
3. 通过验收后再开始阶段二
4. 阶段三只在前两阶段稳定后再进入

## 13. 新文档与旧实现的关系

当前仓库里已经有一版偏“持仓中心”的阶段一原型。

本组新文档的处理原则是：

- 代码可以复用
- 数据结构可以复用
- 页面布局和产品语义允许改造
- 如旧实现与新文档冲突，以新文档为准
