# 阶段五技术方案

## 1. 目标

阶段五的技术目标，是在阶段四线程式研究工作区之上增加一个稳定的：

`显式线程研究记忆层 + 显式会话上下文压缩层 + 可解释的问题路由层 + 显式研究任务层 + 研究反馈闭环层`

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

阶段五第二轮 本轮新增：

- `stock_analysis_research_task` 模型与仓储
- `StockAnalysisQuestionRouterService`
- `StockAnalysisResearchTaskService`
- `GET/POST` 形式的 research task list / detail / create / generate / complete / reopen / dismiss API
- prompt 中的 `Question Routing`
- assistant metadata 中的 `question_intent / response_strategy / routing_reason / recommended_next_action`
- 工作区里的 research task panel、手动创建、生成、完成 / 重开 / 忽略

阶段五第三轮 本轮新增：

- `StockAnalysisExecutionPlannerService`
- `stock_analysis_execution_plan.py`
- `execution planning`
- `task-driven research`
- `validation_summary`
- `execution trace`
- `research_task_id` message input

阶段五第四轮 本轮新增：

- `stock_analysis_research_feedback` 模型与仓储
- `StockAnalysisResearchFeedbackService`
- `GET/POST` 形式的 research feedback list / detail / capture / refresh API
- 研究结果反馈 `outcome_alignment_status`
- 研究过程归因 `process_quality_status + compare/refresh/tooling/validation helpful`
- `what_helped / what_hurt / process_adjustments / task_followup_suggestions`
- 工作区中的 feedback panel、历史列表、最新 feedback 摘要和 assistant message 显式生成入口

当前未实现：

- 自动长期记忆系统
- 更强 planner 语义
- 自动交易
- 更完整的全局绩效与研究看板
- 更强的多步工具编排
- 更强 multi-step autonomous planning

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
- `stock_analysis_research_task`
- `stock_analysis_research_feedback`

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
- `StockAnalysisResearchTaskRepository`
- `StockAnalysisResearchFeedbackRepository`

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
- `StockAnalysisQuestionRouterService`
- `StockAnalysisResearchTaskService`
- `StockAnalysisExecutionPlannerService`
- `StockAnalysisResearchFeedbackService`

职责：

- 读取线程、context cards、conversation history
- 生成 capture / refresh payload
- 失败时走 fallback payload
- 保证线程内 active memory 唯一
- 返回带版本号与统计信息的 memory DTO
- 生成 active compression、recent raw messages 和 compression recommendation
- 在 planner 之前稳定输出 question routing
- 从 memory / compression / compare / refresh / assistant routing 中显式生成 research tasks
- 在 tool planner 之前稳定输出 execution plan
- 生成 validation summary、task update suggestions 与 execution trace
- 基于 anchor assistant message 重新读取 outcome / effectiveness / risk / tasks 并生成 feedback snapshot
- 生成显式 attribution、process adjustments 和 task follow-up suggestions

### 3.4 Prompt Assembler 联动

`StockAnalysisContextAssembler` 扩展：

- 增加 `active_memory` 入参
- 增加 `active_compression` 与 `recent_raw_messages` 入参
- 增加 `question_routing` 入参
- 增加 `execution_plan` 入参
- 在 prompt 中追加 `Thread Active Research Memory`
- 在 prompt 中追加 `Thread Active Conversation Compression`
- 在 prompt 中追加 `Question Routing`
- 在 prompt 中追加 `Execution Plan`
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
- 在 tool planner 之前先执行 question router
- 在 tool planner 之前再执行 execution planner
- 将 active memory、active compression、recent raw messages 一并传给 assembler
- 将 question routing 作为第一层研究语义，与 tool planner 第二层并存
- 将 execution planner 作为第二层研究路径，与 tool planner 第三层并存
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
-  - `question_intent`
-  - `response_strategy`
-  - `routing_reason`
-  - `recommended_next_action`
-  - `followup_candidates`
-  - `suggested_task_titles`
-  - `execution_plan_summary`
-  - `executed_steps / skipped_steps / failed_steps`
-  - `related_task_ids`
-  - `task_update_suggestions`
-  - `validation_summary`
-  - `thesis_change_hint`
-  - `focus_tickers / focus_themes`

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

### 4.4 Question Routing 主路径

当前第二轮优先采用规则优先的可解释路由：

- 先识别 `summarize_context / explain_reasoning / compare_targets / refresh_state_check / external_evidence_check / challenge_conclusion / update_thesis / define_next_step / context_gap / general_followup`
- 再映射到 `answer_from_context / answer_with_compare_focus / refresh_then_answer / tooling_then_answer / restate_and_recheck / highlight_context_gap / suggest_research_tasks`
- 输出 `routing_reason`、`recommended_next_action`、`followup_candidates` 和 `suggested_task_titles`

该层不替代现有 tool planner，只负责研究语义。

### 4.5 Research Task Generate 主路径

当前第二轮 `generate` 只从现有线程结构中显式抽取任务：

- active memory 的 `key_uncertainties / next_questions / risk_points`
- active compression 的 `open_questions / recent_compare_notes / recent_tooling_notes / recent_evidence_notes`
- compare targets 当前状态
- stale / refresh recommended contexts
- 最近 assistant message 的 routing metadata 与建议任务标题

轻量去重规则：

- 以 `thread_id + title + task_type + status=open` 为 dedupe key
- 命中 open task 时更新摘要和关联字段，不重复插入

### 4.6 Execution Planning 主路径

当前第三轮在 question routing 之上新增 execution planning：

- 输入：thread、context cards、compare targets、active memory、active compression、open tasks、question routing、用户问题、显式 refresh / tooling 要求、可选 `research_task_id`
- 输出：`plan_summary / planning_reason / focus_tickers / focus_themes / related_task_ids / primary_compare_targets / requires_refresh / requires_tooling / requires_validation / steps`

step 当前稳定收口为：

- `inspect_context_cards`
- `inspect_compare_targets`
- `inspect_active_memory`
- `inspect_active_compression`
- `inspect_open_tasks`
- `refresh_stale_contexts`
- `collect_internal_structured_evidence`
- `collect_market_price_evidence`
- `collect_external_evidence`
- `validate_thesis`
- `synthesize_answer`
- `suggest_task_updates`

消息链路中的实际执行结果再回填为：

- `executed_steps`
- `skipped_steps`
- `failed_steps`

### 4.7 Validation Summary

当前第三轮新增保守的 thesis validation 层：

- `thesis_maintained`
- `thesis_weakened`
- `thesis_recheck_needed`
- `thesis_improved`

输出包含：

- `summary`
- `support_points`
- `opposing_points`
- `risk_points`
- `thesis_change_hint`

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

### 5.4 Research Tasks

- `GET /api/v1/stock-analysis/threads/{thread_id}/research-tasks`
- `GET /api/v1/stock-analysis/threads/{thread_id}/research-tasks/{task_id}`
- `POST /api/v1/stock-analysis/threads/{thread_id}/research-tasks`
- `POST /api/v1/stock-analysis/threads/{thread_id}/research-tasks/generate`
- `POST /api/v1/stock-analysis/threads/{thread_id}/research-tasks/{task_id}/complete`
- `POST /api/v1/stock-analysis/threads/{thread_id}/research-tasks/{task_id}/reopen`
- `POST /api/v1/stock-analysis/threads/{thread_id}/research-tasks/{task_id}/dismiss`

列表还返回：

- `open_count`
- `high_priority_open_count`
- `last_generated_at`
- `has_actionable_gap`
- `actionable_gap_summary`

### 5.5 Message Execution Metadata

`POST /api/v1/stock-analysis/threads/{thread_id}/messages`

请求新增可选参数：

- `research_task_id`

assistant message metadata 新增：

- `execution_plan_summary`
- `executed_steps`
- `skipped_steps`
- `failed_steps`
- `related_task_ids`
- `task_update_suggestions`
- `validation_summary`
- `thesis_change_hint`
- `focus_tickers`
- `focus_themes`

## 6. 前端设计

### 6.1 数据访问

新增：

- `frontend/src/api/stock-analysis-thread-memory.ts`
- `frontend/src/types/stock-analysis-thread-memory.ts`
- `frontend/src/api/stock-analysis-thread-compression.ts`
- `frontend/src/types/stock-analysis-thread-compression.ts`
- `frontend/src/api/stock-analysis-research-task.ts`
- `frontend/src/types/stock-analysis-research-task.ts`
- `frontend/src/app/home/components/stock-analysis-execution-trace.tsx`
- `frontend/src/app/home/components/stock-analysis-validation-summary.tsx`

### 6.2 工作区交互

`/home/stock-analysis` 新增：

- 研究记忆面板
- 对话压缩面板
- 研究任务面板
- 当前 active memory 摘要卡
- 当前 active compression 摘要卡
- assistant routing explanation
- `生成研究记忆`
- `整理当前对话`
- `生成研究任务`
- `新建手动任务`
- `刷新当前研究记忆`
- `刷新当前压缩摘要`
- `完成 / 重开 / 忽略研究任务`
- `查看记忆历史`
- `查看压缩历史`
- `查看历史任务`
- 历史版本激活
- `围绕此任务继续研究`
- 当前研究锚点任务提示

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

assistant message 若存在 routing metadata，消息下方显示：

- 本轮问题类型
- 本轮回答策略
- routing reason
- recommended next action
- suggested task titles

assistant message 若存在 execution planning metadata，消息下方显示：

- execution plan summary
- executed steps
- skipped steps
- failed steps

assistant message 若存在 validation / task metadata，消息下方显示：

- validation summary
- thesis change hint
- related task ids
- task update suggestions

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
- `test_stock_analysis_question_router_service.py`
- `test_stock_analysis_research_task_service.py`
- `test_stock_analysis_execution_planner_service.py`
- `test_stock_analysis_research_task_router.py`
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
- assembler 拼入 question routing block
- assembler 拼入 execution plan block
- message metadata 标记 used active memory
- message metadata 标记 used active compression
- message metadata 带出 routing fields
- message metadata 带出 execution / validation / task suggestion fields
- compression recommendation 正确
- generate 从 memory / compression / compare / refresh / routing 中抽任务
- research task dedupe / complete / reopen / dismiss 正确
- execution planner 根据 intent 生成不同 steps
- `research_task_id` 能进入 planning
- validation summary 状态合法
- compare 模式保留 compared tickers
- fork thread + `seed_from_active_memory`
