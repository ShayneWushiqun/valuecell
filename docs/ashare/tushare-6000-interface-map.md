# Tushare 6000 积分接口映射

## 1. 文档目的

本文件用于明确当前项目在 `个人使用、非商业化、Tushare 6000 积分`
前提下，可以直接落地的 A 股短周期数据接口，以及这些接口在系统中的建议用法。

这份文档只覆盖：

- 当前项目真正会用到的接口
- 阶段一和阶段二优先落地的模块
- 6000 积分以内或 5000 积分以内可直接使用的接口

这份文档不覆盖：

- 全量 Tushare 接口百科
- 8000 积分以上专属接口
- 分钟、实时日线、新闻、公告、政策法规等独立付费权限

## 2. 当前数据采购边界

当前默认数据采购方案是：

- `Tushare 6000 积分`
- `个人学习和研究使用`
- `不额外购买独立权限`

在这个边界下，系统可以较稳地实现：

- 市场总览
- 情绪周期与历史轨迹
- 主流题材和板块趋势
- 自选观察
- 持仓处理
- 机会池初筛
- 买点与可交易性轻量判断
- 风险事件排雷

在这个边界下，系统暂时不应默认依赖：

- 实时分钟
- 实时日线
- 新闻资讯库
- 公告全文库
- 政策法规库
- 券商研报库
- 8000 积分以上的强短线特色接口

## 3. 接口分组

### 3.1 市场与价格基础

| 接口 | 用途 | 当前模块 |
| --- | --- | --- |
| `daily` | 个股日线、趋势、涨跌幅、量价结构 | 市场温度、自选观察、持仓处理、机会池 |
| `daily_basic` | 换手、量比、流通市值、基础估值和流通属性 | 自选观察、持仓处理、机会池排序 |
| `daily_info` | 交易所市场统计、板块总览 | 市场总览、情绪周期 |
| `stk_limit` | 每日涨跌停价格，用于可交易性边界 | 可交易性提示、持仓风险、买点判断 |

### 3.2 情绪与短线强弱

| 接口 | 用途 | 当前模块 |
| --- | --- | --- |
| `limit_list_d` | 涨停、跌停、炸板列表 | 市场温度、情绪周期、强弱判断 |
| `kpl_list` | 开盘啦涨停/跌停/炸板榜、板块、连板状态 | 情绪周期、主线题材、核心票识别、机会池 |
| `ths_hot` | 同花顺热榜，辅助判断热度和关注度 | 题材热度、自选观察、机会池排序 |
| `top_list` | 龙虎榜每日明细 | 持仓处理、机会池加权 |
| `top_inst` | 龙虎榜机构明细 | 核心票识别、资金承接确认 |

### 3.3 题材、板块与方向

| 接口 | 用途 | 当前模块 |
| --- | --- | --- |
| `ths_index` | 同花顺概念/行业/主题板块列表 | 主线题材识别、板块数据初始化 |
| `ths_daily` | 同花顺板块指数行情 | 主流题材趋势、板块趋势 |
| `ths_member` | 同花顺板块成分股 | 题材归属、代表股识别、机会池构建 |
| `moneyflow_ind_ths` | 同花顺行业资金流 | 板块强弱、主线题材判断 |
| `moneyflow_ind_dc` | 东方财富概念/行业资金流 | 板块交叉验证、题材资金判断 |
| `tdx_index` | 通达信板块基础信息，作为板块补充源 | 题材补全、板块字典校验 |

### 3.4 个股资金与风险事件

| 接口 | 用途 | 当前模块 |
| --- | --- | --- |
| `moneyflow` | 个股资金流向 | 自选观察、持仓处理、机会池排序 |
| `forecast` / `forecast_vip` | 业绩预告 | 风险排雷、持仓风险、事件监控 |
| `express` / `express_vip` | 业绩快报 | 风险排雷、事件确认 |
| `disclosure_date` | 财报披露日期 | 时间窗提醒、事件风险 |
| `stk_holdertrade` | 股东增减持 | 风险预警、信号修正 |
| `share_float` | 限售解禁 | 风险预警、卖点参考 |

## 4. 当前项目应优先使用的接口

### 4.1 阶段一必用

阶段一推荐优先接入或组织的接口：

- `daily`
- `daily_basic`
- `daily_info`
- `stk_limit`
- `limit_list_d`
- `kpl_list`
- `ths_index`
- `ths_daily`
- `ths_member`
- `moneyflow_ind_ths`
- `moneyflow_ind_dc`
- `moneyflow`
- `ths_hot`
- `disclosure_date`
- `stk_holdertrade`
- `share_float`

### 4.2 阶段二追加重点

阶段二在阶段一基础上重点补强：

- `top_list`
- `top_inst`
- `forecast_vip`
- `express_vip`
- `tdx_index`

说明：

- `forecast` 和 `express` 更适合按单票查询。
- 如果阶段二要做更稳定的全市场风险事件扫描，应优先使用
  `forecast_vip` 和 `express_vip`。

## 5. 模块到接口的映射

### 5.1 `market_pulse_service.py`

目标：

- 给首页生成市场总览
- 输出市场状态和一句话操作建议

建议调用接口：

- `daily_info`
- `limit_list_d`
- `kpl_list`
- `daily`

建议产出：

- 上涨家数 / 下跌家数
- 涨停数 / 跌停数 / 炸板数
- 主板、创业板等成交和强弱概览
- 今日市场状态：进攻 / 轮动 / 震荡 / 修复 / 退潮

说明：

- `daily_info` 是市场总览主接口。
- `limit_list_d` 和 `kpl_list` 用来补强短线强弱和情绪统计。
- `daily` 用于补充指数或代表股涨跌表现。

### 5.2 `emotion_cycle_service.py`

目标：

- 识别当前情绪周期阶段
- 生成过去 5 到 10 个交易日轨迹

建议调用接口：

- `daily_info`
- `limit_list_d`
- `kpl_list`
- `ths_hot`

建议产出：

- 当前情绪阶段
- 最近 5 到 10 日的阶段序列
- 情绪方向：上行 / 横向 / 下行
- 今日操作提示：试错 / 跟随 / 观察 / 防守

说明：

- `limit_list_d` 负责涨停、跌停、炸板基础结构。
- `kpl_list` 负责连板状态、题材原因、炸板补充。
- `ths_hot` 可用于给情绪热度增加一个关注度维度。

### 5.3 `theme_focus_service.py`

目标：

- 生成主流题材和重点方向
- 输出板块趋势和代表股

建议调用接口：

- `ths_index`
- `ths_daily`
- `ths_member`
- `moneyflow_ind_ths`
- `moneyflow_ind_dc`
- `kpl_list`
- `ths_hot`
- `tdx_index`

建议产出：

- 主线题材 / 次主线题材
- 题材状态：加强 / 活跃 / 分歧 / 退潮
- 板块趋势：上行 / 横盘 / 转弱
- 每个方向的代表股和核心票

说明：

- `ths_index + ths_daily + ths_member` 是当前题材层主数据源。
- `moneyflow_ind_ths` 和 `moneyflow_ind_dc` 用来补强板块资金方向。
- `kpl_list` 用来补充短线题材热度和连板代表股。
- `tdx_index` 用于板块字典补充和交叉校验，不是第一主源。

### 5.4 `watchlist_observation_service.py`

目标：

- 给自选股生成观察状态
- 输出一句话原因、角色标签和可交易性提示

建议调用接口：

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

建议产出：

- 观察状态：普通观察 / 重点观察 / 风险观察
- 角色标签：龙头 / 中军 / 跟风 / 弱势
- 趋势质量：顺势 / 震荡 / 拖沓 / 走弱
- 可交易性：可观察 / 可低吸 / 谨慎追高 / 流动性风险
- 一句话原因

说明：

- `ths_member` 用于判断它是否属于当前主线板块。
- `ths_hot` 用于给“热度不足”或“热度升温”做辅助标签。
- `disclosure_date`、`stk_holdertrade`、`share_float` 用于风险排雷。

### 5.5 `holding_action_service.py`

目标：

- 给当前持仓输出短周期动作建议
- 区分继续持有、减仓、卖出、观察

建议调用接口：

- `daily`
- `daily_basic`
- `moneyflow`
- `stk_limit`
- `limit_list_d`
- `top_list`
- `top_inst`
- `forecast_vip`
- `express_vip`
- `disclosure_date`
- `stk_holdertrade`
- `share_float`

建议产出：

- 动作：持有 / 减仓 / 卖出 / 观察
- 时间窗：5 / 10 / 20 个交易日
- 预期状态：延续 / 观察 / 证伪风险
- 可交易性提示
- 风险事件提示

说明：

- 持仓处理比首页观察更需要风险事件和龙虎榜加权。
- 如果阶段一不想接入太多接口，`top_list`、`top_inst`、`forecast_vip`、
  `express_vip` 可以放到阶段二再补。

### 5.6 `risk_control_service.py`

目标：

- 输出总仓位、单票仓位和建仓方式建议

建议直接依赖：

- `market_pulse_service.py`
- `emotion_cycle_service.py`
- `theme_focus_service.py`
- `watchlist_observation_service.py`
- `holding_action_service.py`

说明：

- `risk_control_service.py` 不需要直接调用 Tushare。
- 它基于前面几个服务的结果做规则汇总即可。

### 5.7 `homepage_context_service.py`

目标：

- 把首页需要的全部上下文聚合成一个结构化返回

建议直接依赖：

- `market_pulse_service.py`
- `emotion_cycle_service.py`
- `theme_focus_service.py`
- `watchlist_observation_service.py`
- `holding_action_service.py`
- `risk_control_service.py`

说明：

- 首页聚合层不直接打 Tushare，避免耦合和重复请求。

## 6. 阶段一落地建议

阶段一建议按下面顺序接数据：

1. `daily_info + limit_list_d + kpl_list`
   先把市场总览和情绪周期做出来。
2. `ths_index + ths_daily + ths_member + moneyflow_ind_ths`
   再把主流题材和板块趋势做出来。
3. `daily + daily_basic + moneyflow + stk_limit`
   再把自选观察和持仓处理做出来。
4. `disclosure_date + stk_holdertrade + share_float`
   最后补齐基础风险排雷。

这样可以最快形成：

- 今日市场环境
- 情绪周期轨迹
- 主线题材与板块趋势
- 自选观察
- 基础持仓处理

## 7. 阶段二落地建议

阶段二建议在阶段一基础上再补：

1. `top_list + top_inst`
   增强核心票识别和资金承接判断。
2. `forecast_vip + express_vip`
   建立更稳定的全市场风险排雷。
3. `ths_hot + kpl_list`
   增强题材热度和短线热度排序。
4. `tdx_index`
   用于题材字典补充和交叉校验。

## 8. 当前明确不纳入 6000 积分基线的接口

以下接口当前不应作为默认前提写入实现方案：

### 8.1 8000 积分及以上

- `limit_list_ths`
- `limit_step`
- `limit_cpt_list`

这些接口对强短线系统很有帮助，但不属于当前 6000 积分方案。

### 8.2 独立付费权限

- `news` 类新闻接口
- `announcement` 类公告接口
- `research_report`
- `stk_premarket`
- 实时日线
- 实时分钟

这些接口跟积分无关，需要单独开通权限。

## 9. 实现约束

另一个 AI 编码工具在实现时，应遵守：

- 默认只使用本文件列出的 6000 积分接口
- 不要直接假设新闻、公告、政策库已经可用
- 不要直接使用 8000 积分以上接口
- 如果需要升级到 8000 积分或独立权限，必须单独评估后再改文档和代码

## 10. 实施建议

建议在适配层补出几个清晰的聚合模块，而不是把所有调用直接写在 service 里：

- `tushare_market_gateway.py`
- `tushare_theme_gateway.py`
- `tushare_risk_gateway.py`
- `tushare_hotness_gateway.py`

如果当前仓库已有 `tushare_adapter.py`，也可以先在同一适配层中按模块拆方法，
不强制立刻新增很多文件。
