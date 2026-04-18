# 阶段五需求文档

## 1. 阶段名称

`研究结论沉淀与线程记忆 MVP`

## 2. 阶段目标

阶段五第一轮的目标，不是再加一个新的聊天框，而是把阶段四已经可用的股票分析线程升级成一个：

`可持续研究的显式研究对象`

用户在同一线程里聊了一段之后，应能显式生成、查看、切换和刷新当前线程的研究记忆，而不需要只靠很长的历史消息回忆上下文。

## 2.1 当前落地状态

阶段四核心 MVP 已完成六轮，已经具备：

- 线程式工作区
- 显式上下文卡片
- compare targets
- 多轮聊天
- `context_only / need_tooling / user_forced_tooling`
- 内部补数、日线价格补数、外部补数第一版
- save-evidence、refresh、refresh-before-answer、provider attempts / fallback chain

阶段五第一轮在此基础上新增：

- 线程研究记忆快照模型 `stock_analysis_thread_memory`
- 显式 `capture / activate / refresh / history` API
- 工作区中的研究记忆面板与历史版本列表
- active memory 参与后续问答的 prompt context
- assistant metadata 和消息区中的“本轮参考了当前线程研究记忆”说明
- fork thread 时可选 `seed_from_active_memory`

当前仍未落地：

- 自动长期记忆系统
- 黑盒自动 memory 注入
- 自动周期性总结
- 自动交易
- 更复杂的研究归因与绩效反馈

## 3. 产品核心问题

阶段五第一轮需要解决的问题是：

- 线程聊久之后，如何把关键信息沉淀成结构化研究结论
- 用户切回线程时，如何快速看到“当前结论”而不是重新翻完整历史
- 后续继续聊时，Agent 如何显式参考现有研究结论，但不压过当前 context cards
- 历史研究结论如何保留版本，方便手动切换而不是被自动覆盖

## 4. 核心定位

阶段五第一轮不是“自动长期记忆中心”，更不是“全局黑盒 memory”。

它的定位是：

`线程级、显式可见、可手动控制的研究记忆快照层。`

## 5. 核心概念

### 5.1 线程研究记忆

每份研究记忆都对应某个线程在某一时刻的研究快照，至少包含：

- 研究摘要
- 当前倾向
- 主要支持依据
- 主要反对 / 分歧依据
- 风险点
- 失效条件
- 关键不确定项
- 下一步问题与待核对数据

### 5.2 Active Memory

线程同一时刻只允许一份 active memory。

active memory 用于：

- 在工作区显式展示当前研究结论
- 参与后续 prompt context
- 作为 fork thread 时可选的初始研究记忆基础

### 5.3 版本历史

capture 和 refresh 都生成新的显式快照，不覆盖旧历史。

用户可以：

- 查看历史版本
- 手动激活某个历史记忆
- 继续基于当前 active memory 研究

## 6. 必做功能

### 6.1 独立研究记忆模型

阶段五第一轮必须提供独立持久化对象 `stock_analysis_thread_memory`，至少覆盖：

- 标题、摘要、倾向、置信度、时间尺度
- focus tickers / themes
- compared tickers
- support / opposing / risk / uncertainties / invalidation / next questions
- linked context ids / linked message ids / linked compare targets
- source snapshot
- `is_active`

### 6.2 显式动作

必须提供以下显式动作：

- `GET /api/v1/stock-analysis/threads/{thread_id}/memories`
- `GET /api/v1/stock-analysis/threads/{thread_id}/memories/{memory_id}`
- `POST /api/v1/stock-analysis/threads/{thread_id}/memories/capture`
- `POST /api/v1/stock-analysis/threads/{thread_id}/memories/{memory_id}/activate`
- `POST /api/v1/stock-analysis/threads/{thread_id}/memories/{memory_id}/refresh`

边界要求：

- `GET` 只读
- 不在发送消息时偷偷自动生成 memory
- `capture / refresh` 才有副作用

### 6.3 研究记忆生成

研究记忆生成要优先走稳定结构化路径：

- 线程 title / focus type
- 当前 context cards
- compare targets
- 最近关键消息
- 最近 refresh 摘要
- 最近 tool evidence 摘要

如果主路径失败，必须 fallback 到保守模板化摘要，不能让接口 500。

### 6.4 显式展示

工作区必须新增研究记忆面板，至少展示：

- 当前 active memory
- 版本数
- 上次更新时间
- stance / confidence / time_horizon
- 依赖 context 数 / compare target 数
- 历史版本摘要与激活入口

### 6.5 聊天联动

如果线程存在 active memory：

- `StockAnalysisContextAssembler` 必须在 prompt 中增加独立的 `Thread Active Research Memory` 分段
- assistant metadata 必须说明本轮是否用了 active memory，以及对应 memory id / title / version / 更新时间
- 前端消息区必须轻量提示“本轮回答参考了当前线程研究记忆”

## 7. 本轮明确不做

- 不做自动后台周期性总结
- 不做全局长期记忆中心
- 不做黑盒自动 memory 注入
- 不做复杂 diff 可视化
- 不做自动交易
- 不做 planner 大改
- 不做每次发消息都自动生成 memory
