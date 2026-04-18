# 阶段四技术方案

## 1. 目标

阶段四的技术目标，不是再接一个普通聊天接口，而是建立一个稳定的：

`股票分析会话编排层`

让系统可以在现有短周期结构化判断之上，支持：

- 线程式研究
- 显式上下文挂载
- 多股票对比
- 按需调用外部工具
- 与现有 TradingAgents、机会池、持仓、题材雷达和提醒中心联动

## 1.1 当前实现阶段

阶段四当前已完成：

- 第一轮：
  - `stock_analysis_thread`
  - `analysis_context_card`
  - `StockAnalysisWorkspaceService`
  - TradingAgents run 导入
  - `/home/stock-analysis` 三栏骨架
- 第二轮：
  - 统一 `context-import` 扩展到 `holding / opportunity / watchlist / theme / alert / ticker`
  - `StockAnalysisContextAssembler`
  - `StockAnalysisMessageService`
  - `GET /api/v1/stock-analysis/threads/{thread_id}/messages`
  - `POST /api/v1/stock-analysis/threads/{thread_id}/messages`
  - 线程历史跟随 `conversation_id` 回看
  - 前端工作区聊天区与多页面研究线程入口

阶段四当前未实现：

- 外部工具补数
- `need_tooling` / `user_forced_tooling`
- 独立 `StockAnalysisToolPlanner`
- 复杂流式可视化

## 2. 设计原则

### 2.1 不重做聊天基础设施

当前仓库已经具备：

- `conversation`
- `agent_stream`

阶段四应优先复用这套基础设施，而不是再造一套新的聊天系统。

### 2.2 线程与上下文分离

线程不等于上下文集合。

同一个线程在不同时间可以挂不同的上下文卡片；同一个研究主题也可以复制出新线程做分叉研究。

### 2.3 上下文必须显式

系统不能依赖“黑盒式隐式记忆一切”。

真正参与推理的，应始终是线程当前可见的上下文卡片集合。

### 2.4 先用已有系统语义，再考虑外部补数

回答顺序应是：

1. 先使用当前系统已沉淀的结构化语义
2. 不足时再使用结构化行情工具
3. 最后才考虑新闻和解释型外部数据

### 2.5 补数与长期上下文挂载分离

一次回答里临时调用的外部工具结果，不应自动变成长期上下文。

更合理的方式是：

- 工具结果先作为临时证据补充
- 用户确认后，才显式加入上下文卡片

### 2.6 不把 TradingAgents 改造成聊天系统

`TradingAgents` 应继续做：

- run 管理
- 报告输出

阶段四只把它作为一个高质量上下文来源，不把它本体重构成聊天页。

## 3. 核心分层

建议阶段四新增以下分层。

### 3.1 研究线程层

负责：

- 新建线程
- 复制线程
- 删除线程
- 重命名线程
- 列出线程

### 3.2 上下文卡片层

负责：

- 把不同模块的结构化结果统一转换为上下文卡片
- 线程与卡片的挂载关系
- 卡片的追加、替换、删除、置顶

### 3.3 上下文装配层

负责：

- 读取当前线程下的卡片
- 抽取 ticker refs / theme refs
- 生成 prompt context
- 汇总当前可直接回答的信息
- 判断当前缺失的信息

### 3.4 提问执行策略层

负责：

- 判断本次提问使用哪种回答模式
- 决定是否需要补数据
- 决定调用哪一层工具
- 把最终上下文交给底层流式 Agent

当前第二轮的落地方式先做保守收口：

- 不做 tool planner
- 不触发外部工具
- 只做 `context_only`
- 通过 `StockAnalysisMessageService` 直接复用 conversation 基础设施和稳定 agent 能力

### 3.5 流式执行层

底层仍复用当前：

- `agent_stream`
- `conversation`

阶段四不应重造流式协议。

## 4. 建议新增对象模型

### 4.1 `stock_analysis_thread`

建议新增线程模型，字段至少包括：

- `thread_id`
- `user_id`
- `title`
- `focus_type`
- `ticker_refs_json`
- `theme_refs_json`
- `conversation_id`
- `created_at`
- `updated_at`
- `archived_at`

`focus_type` 可先收口为：

- `ticker`
- `theme`
- `comparison`
- `holding`
- `tradingagents_followup`
- `mixed`

### 4.2 `analysis_context_card`

建议新增上下文卡片模型，字段至少包括：

- `context_id`
- `thread_id`
- `user_id`
- `context_type`
- `title`
- `subtitle`
- `ticker_refs_json`
- `theme_refs_json`
- `summary`
- `snapshot_payload_json`
- `source_module`
- `source_ref`
- `staleness_hint`
- `is_pinned`
- `created_at`
- `updated_at`

`context_type` 建议先支持：

- `tradingagents_run`
- `holding`
- `opportunity`
- `watchlist`
- `theme`
- `alert`
- `ticker`

## 5. 上下文卡片的统一协议

阶段四建议引入统一后端对象：

`AnalysisContextCard`

无论来源于哪个模块，最终都转成统一协议。

建议字段：

- `context_id`
- `context_type`
- `title`
- `subtitle`
- `ticker_refs`
- `theme_refs`
- `summary`
- `snapshot_payload`
- `source_ref`
- `source_module`
- `staleness_hint`
- `is_pinned`

其中：

- `summary` 用于模型快速理解这张卡的核心含义
- `snapshot_payload` 用于结构化细节输入

## 6. 与现有系统的衔接方式

### 6.1 与 TradingAgents 的衔接

建议新增一层 adapter，把某次 TradingAgents run 转成上下文卡片。

推荐第一版只生成一张总卡：

- `TradingAgents 分析摘要`

后续如果有需要，再拆成：

- 最终结论
- 市场观点
- 新闻观点
- 基本面观点

### 6.2 与持仓、机会池、观察池、题材雷达的衔接

这些模块当前已经有结构化输出，阶段四更适合新增：

- `context builder`
- 或 `context adapter`

把它们统一转为 `AnalysisContextCard`。

### 6.3 与决策上下文、时间窗、review 的衔接

这些模块更适合作为高价值上下文来源：

- `decision_context_window`
- `decision_record`
- `decision_outcome_review`

它们可以直接作为“高级研究卡片”挂进线程。

## 7. 建议新增服务

### 7.1 `StockAnalysisWorkspaceService`

这是阶段四最核心的编排服务。

建议它不要直接负责大模型推理，而是负责：

- 线程管理
- 上下文卡片管理
- prompt context 装配
- 工具层选择
- 调用底层流式执行入口

当前实现已收口为：

- 线程管理
- 上下文卡片管理
- 多模块 context import
- 工作区 overview 聚合

消息执行已独立到 `StockAnalysisMessageService`，避免把工作区编排层和聊天执行层混在一起。

### 7.2 `StockAnalysisContextAssembler`

建议把上下文装配拆成独立模块，避免 `StockAnalysisWorkspaceService` 变成超大 service。

职责包括：

- 读取当前线程的卡片
- 提取 ticker refs / theme refs
- 生成：
  - 研究主题摘要
  - 当前已有判断
  - 当前冲突点
  - 当前缺口点

### 7.3 `StockAnalysisToolPlanner`

建议把工具调用策略也拆开。

职责包括：

- 判断当前问题是否能直接回答
- 判断当前缺的是哪类数据
- 选择工具层级
- 输出本轮工具调用理由

### 7.4 `StockAnalysisMessageService`

建议增加一个更靠近提问执行的 service，负责：

- 接收用户消息
- 读取线程当前上下文
- 调用 tool planner
- 调用底层流式入口
- 记录本轮消息的依据说明和工具调用说明

当前第二轮已实现：

- 根据 `thread_id` 查找 `conversation_id`
- 读取线程当前上下文卡片
- 调用 `StockAnalysisContextAssembler` 生成分段 prompt context
- 读取并返回当前线程消息历史
- 写入 user / assistant message
- 在 metadata 中返回：
  - `answer_basis = context_only`
  - `used_context_ids`
  - `missing_context_hints`

## 8. 建议新增 API

### 8.1 线程管理

- `GET /api/v1/stock-analysis/threads`
- `POST /api/v1/stock-analysis/threads`
- `PUT /api/v1/stock-analysis/threads/{thread_id}`
- `POST /api/v1/stock-analysis/threads/{thread_id}/duplicate`
- `DELETE /api/v1/stock-analysis/threads/{thread_id}`

### 8.2 上下文卡片管理

- `GET /api/v1/stock-analysis/threads/{thread_id}/contexts`
- `POST /api/v1/stock-analysis/threads/{thread_id}/contexts`
- `PUT /api/v1/stock-analysis/threads/{thread_id}/contexts/{context_id}`
- `DELETE /api/v1/stock-analysis/threads/{thread_id}/contexts/{context_id}`

### 8.3 提问执行

建议不要直接复用通用聊天请求，而是加专用入口：

- `POST /api/v1/stock-analysis/threads/{thread_id}/messages`
- 或
- `POST /api/v1/stock-analysis/threads/{thread_id}/stream`

这个入口应负责：

1. 读取线程上下文
2. 装配 prompt context
3. 判断回答模式
4. 必要时调用工具层
5. 交给底层流式聊天基础设施

### 8.4 入口快捷动作

建议提供统一入口 API，用于从其他模块创建上下文卡片：

- `POST /api/v1/stock-analysis/from-tradingagents-run`
- `POST /api/v1/stock-analysis/from-holding`
- `POST /api/v1/stock-analysis/from-opportunity`
- `POST /api/v1/stock-analysis/from-theme`
- `POST /api/v1/stock-analysis/from-alert`

或者统一成一个：

- `POST /api/v1/stock-analysis/context-import`

第一版推荐统一入口，减少 router 数量。

## 9. 回答模式与工具策略

阶段四建议固定支持三种模式。

### 9.1 `context_only`

仅使用：

- 当前线程上下文卡片
- 当前线程聊天历史

不调用外部工具。

### 9.2 `need_tooling`

当系统判断当前上下文不足时，按需补数据后回答。

### 9.3 `user_forced_tooling`

用户明确要求：

- 补最新消息
- 拉日线
- 再查新闻

时直接进入工具模式。

## 10. 工具层分层

### 10.1 第一层：内部结构化工具

优先复用现有系统能力：

- TradingAgents run
- 持仓、机会池、观察池
- 题材雷达
- 提醒中心
- 决策上下文
- 决策时间窗
- 决策记录与结果回看
- 风控与分仓建议

### 10.2 第二层：结构化行情工具

- Tushare
- 现有 `asset_service`
- 现有 `daily_snapshot`

### 10.3 第三层：外部解释型工具

- 新闻
- YFinance
- 其他后续可接入的解释型来源

工具调用优先级必须遵循：

`内部结构化语义 > 结构化行情数据 > 外部解释型信息`

## 11. 工具调用理由

建议每次工具调用前，都先生成一个内部 `tool_reason` 对象，用来说明：

- 当前上下文缺什么
- 为什么当前问题不能直接回答
- 要调哪个工具

这个对象可以转成用户可见的轻量提示，例如：

- 当前上下文不足以回答最新走势，已补充日线价格数据
- 用户明确要求补新闻后再回答，已补充外部新闻信息

## 12. 线程与 conversation 的关系

建议线程与 conversation 分开存，但建立关联。

推荐方式：

- 一个 `stock_analysis_thread`
- 关联一个 `conversation_id`
- 再关联一组 `analysis_context_card`

这样后续才好支持：

- 复制线程
- 保留上下文但重开会话
- 保留会话但清理上下文

第一版若实现成本较高，也可以简化为：

- 线程稳定绑定一个 conversation

但模型层面不建议硬绑定死。

## 13. 前端页面建议

建议新增统一页面：

- `/home/stock-analysis`

推荐三栏结构：

### 左栏：线程列表

- 线程标题
- 线程标签
- 最近更新时间
- 上下文数

### 中栏：聊天主区

- 对话内容
- 直接提问
- 补数据后再回答
- 回答依据说明

### 右栏：上下文卡片区

- 当前卡片列表
- 卡片详情
- 添加上下文入口

## 14. 推荐实现顺序

阶段四建议按下面顺序推进：

1. 先做线程模型和上下文卡片模型
2. 再做工作区页面和上下文管理
3. 再做 TradingAgents、持仓、机会池等入口联动
4. 再做提问执行策略层
5. 最后再逐步接外部工具调用

## 15. 测试重点

阶段四不应只验证“能聊起来”，还需要重点测试：

- 线程之间上下文不串
- TradingAgents run 能正确转卡片
- 上下文卡片可追加、可替换、可删除
- 默认模式不乱调工具
- 缺信息时才会进入工具模式
- 用户强制补数时能正确调用工具层
- 线程复制后，上下文与消息历史边界正确

## 16. 当前阶段定位

阶段四应理解为：

`把现有结构化短周期决策系统，扩展为一个线程式、多上下文、可持续研究的股票分析会话工作区。`

它不替代现有页面，而是把现有页面的高价值结果组织成可以继续研究和追问的会话层。
