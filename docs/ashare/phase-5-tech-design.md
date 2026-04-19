# 阶段五技术方案

## 1. 目标

阶段五第一轮的技术目标，是在阶段四线程式研究工作区之上增加一个稳定的：

`显式线程研究记忆层 + 显式会话上下文压缩层`

让系统既能保留线程的长期研究结论，又继续坚持：

- 显式上下文优先
- 显式 compare targets 优先
- active memory 仅作为线程级研究摘要辅助
- active compression 仅作为较早消息历史的显式压缩辅助
- recent raw messages 保留最近一轮对话细节

## 1.1 当前实现阶段

阶段四核心 MVP 已完成六轮，阶段五第一轮-A 已新增：

- `stock_analysis_thread_memory` 模型与仓储
- `StockAnalysisThreadMemoryService`
- `GET/POST` 形式的 list / detail / capture / activate / refresh API
- prompt 中的 `Thread Active Research Memory`
- assistant metadata 中的 active memory 使用说明
- 工作区里的 memory panel / history / activate / refresh
- fork thread 的 `seed_from_active_memory`

阶段五第一轮-B 本轮新增：

- `stock_analysis_thread_compression` 模型与仓储
- `StockAnalysisThreadCompressionService`
- `GET/POST` 形式的 compression list / detail / capture / activate / refresh API
- prompt 中的 `Thread Active Conversation Compression` 和 `Recent Raw Messages`
- assistant metadata 中的 active compression 使用说明
- 工作区里的 compression panel / history / activate / refresh
- compression recommendation / reason / uncompressed_message_count / estimated_history_size

当前未实现：

- 自动长期记忆系统
- 更强 planner 语义
- 自动交易
- 更复杂的研究归因与绩效反馈

## 2. 设计原则

### 2.1 研究记忆必须显式

研究记忆是可见对象，不是黑盒 prompt 注入。

因此：

- 必须有独立 API
- 必须有显式面板和历史列表
- capture / refresh 必须是显式 POST 动作

### 2.2 上下文卡片优先于研究记忆

active memory 只是一份线程级研究摘要。

当 active memory 与当前 context cards / compare targets 冲突时：

- 以后者为准
- assistant 在 prompt rules 中也要得到这条约束

### 2.3 版本化优先于覆盖

为避免线程研究结论被静默重写：

- capture 生成新版本
- refresh 生成新版本
- activate 只切当前 active，不删除旧历史

### 2.4 稳定 fallback 优先

研究记忆和 compression 生成都可以优先走结构化提炼，但必须保证：

- 生成失败不影响接口可用性
- fallback 至少能基于最近消息、上下文卡片和 compare targets 产出保守 memory / compression

## 3. 核心分层

### 3.1 数据层

新增模型：

- `stock_analysis_thread_memory`
- `stock_analysis_thread_compression`

关键字段：

- `thread_id / user_id`
- `title / summary / stance / confidence / time_horizon`
- `focus_tickers_json / focus_themes_json / compared_tickers_json`
- `support_points_json / opposing_points_json / risk_points_json`
- `key_uncertainties_json / invalidation_conditions_json`
- `next_questions_json / next_data_to_check_json`
- `linked_context_ids_json / linked_message_ids_json / linked_compare_targets_json`
- `source_snapshot_json`
- `is_active`

### 3.2 Repository 层

新增：

- `StockAnalysisThreadMemoryRepository`
- `StockAnalysisThreadCompressionRepository`

提供：

- `list_memories`
- `get_memory_by_id`
- `get_active_memory`
- `create_memory`
- `update_memory`
- `deactivate_thread_memories`
- `list_compressions`
- `get_compression_by_id`
- `get_active_compression`
- `create_compression`
- `update_compression`
- `deactivate_thread_compressions`

### 3.3 Service 层

新增：

- `StockAnalysisThreadMemoryService`
- `StockAnalysisThreadCompressionService`

职责：

- 读取线程、context cards、conversation history
- 生成 capture / refresh payload
- 失败时走 fallback payload
- 保证线程内 active memory 唯一
- 返回带版本号与统计信息的 memory DTO
- 生成 active compression、recent raw messages 和 compression recommendation

### 3.4 Prompt Assembler 联动

`StockAnalysisContextAssembler` 扩展：

- 增加 `active_memory` 入参
- 增加 `active_compression` 与 `recent_raw_messages` 入参
- 在 prompt 中追加 `Thread Active Research Memory`
- 在 prompt 中追加 `Thread Active Conversation Compression`
- 在 prompt 中追加 `Recent Raw Messages`
- 在 response rules 中明确：
  - active memory 是辅助摘要
  - 显式 context cards 与 compare targets 优先
-  - active compression 只负责折叠较早消息历史
-  - recent raw messages 负责保留最新对话细节

### 3.5 Message Service 联动

`StockAnalysisMessageService` 扩展：

- 发送消息时查询 active memory
- 发送消息时查询 active compression 和 recent raw messages
- 将 active memory、active compression、recent raw messages 一并传给 assembler
- assistant metadata 返回：
  - `used_active_memory`
  - `active_memory_id`
  - `active_memory_title`
  - `active_memory_updated_at`
  - `active_memory_version`
-  - `used_active_compression`
-  - `active_compression_id`
-  - `active_compression_title`
-  - `active_compression_updated_at`
-  - `active_compression_version`
-  - `active_compression_covered_until_message_id`
-  - `active_compression_covered_message_count`
-  - `recent_raw_message_count`

### 3.6 Workspace / Fork 联动

`StockAnalysisWorkspaceService.fork_thread(...)` 扩展：

- 新增 `seed_from_active_memory`
- 仍然不复制旧聊天历史
- 若开启 seed，则把源线程 active memory 克隆为新线程的首份初始 memory
- 初始 memory 的 `linked_message_ids_json` 清空，避免把旧线程消息引用带过去

## 4. 研究记忆与对话压缩生成策略

### 4.1 研究记忆主路径

当前第一轮采用稳定的结构化提炼策略，输入包括：

- thread title / focus type
- context cards
- compare targets
- 最近用户与 assistant 关键消息
- 最近 refresh 摘要
- 最近 temporary evidence 标题

提炼输出包括：

- summary
- stance
- confidence
- time_horizon
- support / opposing / risk / uncertainty / invalidation / next steps

### 4.2 Compression 主路径

当前第一轮-B 采用稳定的结构化压缩策略，输入包括：

- recent message history
- compare targets
- 最近 refresh 摘要
- 最近 tooling / evidence 摘要
- active memory
- 当前 context cards

输出包括：

- summary
- current_focus
- covered_until_message_id / covered_message_count
- resolved_topics / open_questions
- recent compare / refresh / tooling / evidence notes
- next_questions

### 4.3 Fallback 路径

若主路径异常：

- 记录 warning
- 回退到保守模板
- 继续返回一份最小可用 memory / compression

fallback 仍保留：

- linked contexts
- linked messages
- compare targets
- source snapshot

## 5. API 设计

### 5.1 列表与详情

- `GET /api/v1/stock-analysis/threads/{thread_id}/memories`
- `GET /api/v1/stock-analysis/threads/{thread_id}/memories/{memory_id}`

列表返回：

- `active_memory`
- `items`
- `count`
- `generated_at`

### 5.2 Capture / Activate / Refresh

- `POST /api/v1/stock-analysis/threads/{thread_id}/memories/capture`
- `POST /api/v1/stock-analysis/threads/{thread_id}/memories/{memory_id}/activate`
- `POST /api/v1/stock-analysis/threads/{thread_id}/memories/{memory_id}/refresh`

语义：

- `capture`: 基于当前线程状态生成新快照并设为 active
- `activate`: 切换历史版本为 active
- `refresh`: 参考旧记忆和当前线程状态生成新版并设为 active

### 5.3 Compression List / Capture / Activate / Refresh

- `GET /api/v1/stock-analysis/threads/{thread_id}/compressions`
- `GET /api/v1/stock-analysis/threads/{thread_id}/compressions/{compression_id}`
- `POST /api/v1/stock-analysis/threads/{thread_id}/compressions/capture`
- `POST /api/v1/stock-analysis/threads/{thread_id}/compressions/{compression_id}/activate`
- `POST /api/v1/stock-analysis/threads/{thread_id}/compressions/{compression_id}/refresh`

列表还返回：

- `compression_recommended`
- `compression_reason`
- `uncompressed_message_count`
- `estimated_history_size`
- `active_compression_stale`

## 6. 前端设计

### 6.1 数据访问

新增：

- `frontend/src/api/stock-analysis-thread-memory.ts`
- `frontend/src/types/stock-analysis-thread-memory.ts`
- `frontend/src/api/stock-analysis-thread-compression.ts`
- `frontend/src/types/stock-analysis-thread-compression.ts`

### 6.2 工作区交互

`/home/stock-analysis` 新增：

- 研究记忆面板
- 对话压缩面板
- 当前 active memory 摘要卡
- 当前 active compression 摘要卡
- `生成研究记忆`
- `整理当前对话`
- `刷新当前研究记忆`
- `刷新当前压缩摘要`
- `查看记忆历史`
- `查看压缩历史`
- 历史版本激活

### 6.3 消息区提示

assistant message 若使用 active memory，消息下方显示：

- 本轮回答参考了当前线程研究记忆
- title / version
- updated_at

assistant message 若使用 active compression，消息下方显示：

- 本轮回答参考了当前线程对话压缩摘要
- title / version
- updated_at
- 覆盖到哪条消息
- recent raw message 数量

### 6.4 Fork Dialog 联动

fork dialog 新增：

- `seed_from_active_memory` 复选项

只有当前线程存在 active memory 时才允许勾选。

## 7. 测试策略

后端新增 / 扩展：

- `test_stock_analysis_thread_memory_service.py`
- `test_stock_analysis_thread_memory_router.py`
- `test_stock_analysis_thread_compression_service.py`
- `test_stock_analysis_thread_compression_router.py`
- `test_stock_analysis_context_assembler.py`
- `test_stock_analysis_message_service.py`
- `test_stock_analysis_workspace_service.py`

覆盖重点：

- capture 成功
- synthesis 失败 fallback
- activate 唯一 active
- refresh 生成新版本
- assembler 拼入 active memory
- assembler 拼入 active compression 与 recent raw messages
- message metadata 标记 used active memory
- message metadata 标记 used active compression
- compression recommendation 正确
- compare 模式保留 compared tickers
- fork thread + `seed_from_active_memory`
