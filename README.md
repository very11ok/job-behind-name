# job-behind-name：岗位—任务网络的三条再捆绑准则——LLM 预测 agent 的可检验判定与修复

基于招聘文本衍生的"岗位—任务网络"（job–task network），把三条组织与劳动经济学的"再捆绑"（re-bundling）准则实现为可检验的预测规则：以 **T=2020 年** 的网络结构为前因（antecedent），以 **T+1/2/3 年**（2021–2023）真实涌现的岗位—任务组合为后果（outcome），做"前因 → 若干年后 → 后果"的条件概率判定。LLM 用于前因的主观判定与岗位—任务对的绑定判定；所有统计量（条件概率、提升比、卡方、Spearman）均为确定性计算。本仓库含全部数据、脚本、中间产物与结果文档，可完整复现。

## 三条准则

| # | 准则 | 理论出处 | 单元 | 前因（T=2020） | 后果（T+h） |
|---|------|----------|------|----------------|-------------|
| a | 互补性再捆绑 | Milgrom & Roberts 1995 / Kremer 1993 | 岗位任务集 | 岗位任务集中存在 E 差 ≥2 的知识互补对（LLM 判定） | 任务集变化且新任务对出现高-低 E 搭配（mixed_new） |
| b | 层级解绑 | Garicano 2000 | 任务团（任务共现社区） | 知识不对称度（团内 E_ord 离散度）高；层级数 hier_n≥3 | 分裂出任务集不对称度更低的窄岗位（down_std） |
| c | 模仿性模板扩散 | DiMaggio & Powell 1983 | 企业×年 | 组织规模结构：n_jobs、n_mod 高于中位数 | 新增岗位中"跨企业模板采纳"占比高于同年中位数（above_median） |

## 核心结果（提升比 = P(后果|前因=1) / P(后果|前因=0)，T=2020）

| 准则 / 判据 | h=1 | h=2 | h=3 | 显著性 | 结论 |
|-------------|-----|-----|-----|--------|------|
| a：LLM holds → mixed_new（原版） | **2.38** | **3.00** | **2.57** | 三窗口全显著 | 原生成立 |
| b：asym(e_std)高 → down_std（方向版） | **1.56** | **1.40** | **1.29** | p=4.6e-06/0.003/0.038 | 成立 |
| b：LLM holds ∧ hier_n≥3 → split（门槛版） | **2.34** | **2.59** | **2.49** | p<7.3e-07 | 成立 |
| b：门槛版 ∧ asym 高 → down_std（叠加） | **3.36** | **2.74** | **2.73** | p≤0.006 | 最强（n=15） |
| c：n_jobs高 ∧ n_mod高 → above_median | **2.98** | **3.26** | **3.06** | p=8e-06/2.6e-05/0.0015 | 成立 |
| c：LLM holds（对照，已确认空壳） | 1.27 | 1.72 | 0.98 | 全不显著 | 弃用 |

修复过程要点（详见 `docs/`）：

- 准则 b 的 LLM 原始判定呈**反向**关系（提升比 0.57/0.56/0.49）。诊断发现这是混淆结构：holds=1 的团更小、层级更少、更难整体被拆。门槛扫描（`scan_g2_threshold.py`）确认 hier_n≥3 为最优切分；方向性重构（`verify_g2_direction.py`）把后果改为"拆出的窄岗位不对称度更低"后关系转正。附带发现：拆出的窄岗位平均知识强度**更高**（down_e 提升比 0.25，强反向），即实际机制是"知识密集任务剥离成专家岗"（知识层从执行层剥离），而非"例程下沉"，同样符合 Garicano 的知识型层级逻辑。
- 准则 c 的 LLM 判定确认为空壳（p 档排序力≈0，成立率 82.5%）。客观指标扫描（`scan_g3_metrics.py`）发现 n_jobs/n_mod 是最优替代前因；所有相似度指标（surf/struct/xfirm）无效或反向。
- 全部关键数字经 `recheck_results.py` / `recheck_g2fix.py` 用 scipy.stats 独立交叉验证，逐位吻合。

## 仓库结构

```
├── README.md                        本文件
├── docs/
│   ├── workflow.md                  LLM 判定 workflow 的 8 节详细说明
│   ├── report.md                    全流程实验报告
│   └── results/*.md                 全部结果文档
├── scripts/
│   ├── *.py                         主流程脚本（见"脚本索引"）
│   ├── jtagent/*.py                 核心库：快照 IO / 相似度 / 属性 / LLM 客户端 / 规则
│   └── workflow/pipeline.dwf.ts     66 批 LLM 前因判定的 dynamic workflow 脚本
└── data/
    ├── snapshots/                   任务网络年度快照（2016–2026，23 个 parquet）
    ├── pairs/                       任务对相似度年度面板（2018–2025，13 个 parquet，约 376MB）
    ├── objects/                     三准则对象池 + 后果标签 + LLM 前因判定（9 个 parquet）
    ├── results/                     全部结果表（csv/parquet）
    ├── judge_input/                 66 批 LLM 前因判定输入（PROTO 协议文本）
    ├── anno_input_2019/             2019 绑定判定人工标注材料（120 批 csv）
    ├── anno_output_2019/            2019 标注回收与构建脚本
    └── pair_judge_truth.parquet     岗位—任务对绑定判定的真值集（人工标注 + LLM 对照）
```

## 数据字典

### data/snapshots/（任务网络快照）

- `jobs_YYYY.parquet`（YYYY=2016…2026）：`job` 岗位 ID、`tasks` 任务 ID 列表、`name` 岗位名、`firm` 企业、`industry` 行业、`exposure` AI 暴露度、`n_postings` 招聘帖子数。
- `edges_YYYY.parquet`：岗位—任务边（`job`、`task`）。
- `task_dict.parquet`：任务字典。`task` ID、`task_text` 任务文本、`soc`/`occupation` 职业分类、`E`/`E_human` 知识强度标注、`auto` 可自动化标注、`E_ord` 知识强度数值（1–5，准则 b 不对称度 asym 的计算基数）。

### data/pairs/（任务对相似度面板，2018–2025）

`pairs_YYYY.parquet`：任务对 `ti, tj` 及特征——共邻数 `cn`、度 `deg_*`、优先连接 `pa`、Jaccard、知识强度 `E_ord_*`、上下文 `ctx_*`、可编码度 `codable_*`、模块归属 `module_*`、知识差 `E_gap`；`y`/`y_new` 绑定延续/新增标签；`bind_TM1` 上年绑定。用途：准则 a/b 任务对层面的预测底料。由 `scripts/jtagent/pairs.py` 从 snapshots 重算。

> 文件拆分说明：GitHub 单文件限制约 40MB，2019/2020/2023 年为完整单文件；2018/2021/2022/2024/2025 年按行对半拆为 `_part1/_part2`（各 250 万行），读取时 `pd.concat([pd.read_parquet(p1), pd.read_parquet(p2)])` 即可无损还原。拆分脚本：`scripts/split_pairs.py`。

### data/objects/（三准则对象池，T=2020）

- `g1_jobs_2020.parquet`（2000 岗位）：`job`、`size` 任务数、`tasks`/`e_ord`/`cod`/`ctx`/`mod` 任务属性串、`has_E2`/`has_E0` 高低知识任务标记、`n_mod` 模块数。对齐键 `job`。
- `g2_comm_2020.parquet`（1502 任务团）：`seed` 种子任务、`comm` 社区、`size` 团规模、`tasks`、`e_ord`、`hier`、`mod`、`n_mod`、`e2_share` 编码任务占比、`hier_n` 层级数。对齐键 `seed`。
- `g3_firms_2020.parquet`（307 企业）：`firm`、`n_jobs` 岗位数、`mean_size`、`n_mod`、`e2_share`、`struct_sim`/`xfirm_sim`/`surf_sim` 结构/跨企业/表层相似度。对齐键 `firm`。
- `labels_g1_2020.parquet`：`job, h, alive, changed, n_new_pairs, n_mixed_new_pairs, mixed_new`（准则 a 后果）。
- `labels_g2_2020.parquet`：`seed, h, n_holders, cover, split`（准则 b 后果：被 ≥2 个窄岗位承载且覆盖 ≥60%）。
- `labels_g3_2020.parquet`：`firm, h, n_new_jobs, adopt_share, adopt_mean_sim, above_median, median_adopt`（准则 c 后果）。
- `judge_g1/g2/g3_2020.parquet`：LLM 前因判定，`holds`(0/1)、`p` 置信档、`why` 理由、`batch` 批次号。

### data/results/（结果表）

- 修复验证明细：`g2_threshold_scan`（门槛扫描）、`g2_threshold_combo`（联合门槛）、`g2_fix_verify`（门槛版验证）、`g2_direction_verify`（方向版验证）、`g3_metric_scan`/`g3_metric_corr`（指标扫描）、`g3_fix_verify`（准则 c 修复验证），各有 .md（在 docs/results/）与 .parquet。
- `rule_c_adoption.csv/.parquet`（准则 c 底料）：每新增岗位的 `struct_sim`、`xfirm_struct_sim`、`surf_sim`、匹配模板 `tmpl_*`、`cross_firm`、`surf_resid`。
- `split_events.csv` 分裂事件、`firm_year_jobs.parquet` 与 `firm_year_stats.csv` 企业×年面板、`agent_metrics_2019.csv`、`baseline_metrics.csv`、`ablation_feats_*` 2019 预测实验消融、`signature_trend.csv`、`snapshot_summary.csv`、`candidate_summary.csv`、`anno_2019.parquet` 与 `agent_preds_2019_sample.parquet`（2019 标注实验）。

### data/judge_input/ 与 data/pair_judge_truth.parquet

- `judge_input/*.txt`：66 批 LLM 前因判定输入，PROTO 判定协议 + BATCH 明细，与 `judge_g*_2020.parquet` 的 `batch` 字段对应。
- `pair_judge_truth.parquet`：岗位—任务对绑定判定真值集（2019 人工标注 + LLM 对照），含任务文本、特征、`A_互补再捆绑`/`B_层级解绑` 等标注列。

### data/anno_input_2019/ 与 data/anno_output_2019/

2019 年岗位—任务对绑定判定的人工标注材料（120 批 csv 输入 + 回收标注与构建脚本），是 `pair_judge_truth.parquet` 与准则 a/b 校准的来源。

## 脚本索引（scripts/，按执行顺序）

1. `jtagent/io_snapshot.py` — 快照加载；`jtagent/pairs.py` — 任务对面板构建
2. `jtagent/attrs.py` / `features.py` / `firm_panel.py` / `rule_c.py` — 任务属性、特征、企业面板、模板采纳
3. `objects.py` — 构建三准则对象池 → `data/objects/g*_2020.parquet`
4. `outcomes.py` — 生成后果标签 → `labels_g*_2020.parquet`
5. `prep_judge_input.py` — 生成 66 批判定输入 → `data/judge_input/`
6. `workflow/pipeline.dwf.ts` — LLM 判定 workflow（66 批 fan-out + 补标）
7. `merge_judge.py` — 合并判定与标签 → `judge_g*_2020.parquet`
8. `reverse_outcome.py` / `diagnose_g2.py` / `diagnose_g3.py` — 反向概率与诊断
9. `scan_g2_threshold.py` / `verify_g2_fix.py` — 准则 b 门槛扫描与验证
10. `verify_g2_direction.py` — 准则 b 方向性重构验证
11. `scan_g3_metrics.py` / `verify_g3_fix.py` — 准则 c 指标扫描与修复验证
12. `recheck_results.py` / `recheck_g2fix.py` — scipy 独立复核
13. `run_agent_2019.py` / `run_backtest.py` / `ablation_feats.py` / `make_figures.py` / `trends.py` — 2019 预测实验与图表

## 复现

```bash
# 1. 对象池 + 后果标签（T=2020）
python objects.py && python outcomes.py
# 2. 判定输入（66 批）→ 用 workflow 引擎跑 workflow/pipeline.dwf.ts → 合并
python prep_judge_input.py && python merge_judge.py
# 3. 三准则修复验证
python verify_g2_fix.py && python verify_g2_direction.py && python verify_g3_fix.py
# 4. 独立复核（scipy 交叉验证）
python recheck_results.py && python recheck_g2fix.py
```

依赖：`pandas pyarrow numpy scipy`。LLM 客户端（`jtagent/llm.py`）从环境变量 `JTAGENT_ENDPOINTS` 读取端点配置（JSON：`[{"baseURL":..., "apiKey":..., "name":...}]`），仓库不含任何凭据。

## 结果文档索引（docs/results/）

`antecedent_outcome_2020.md`（主表）· `reverse_outcome_antecedent_2020.md`（反向概率）· `diagnose_g2_g3.md`（混淆诊断）· `g2_threshold_scan.md`（门槛扫描）· `g2_fix_verify.md`（门槛版验证）· `g2_direction_verify.md`（方向版验证）· `g3_metric_scan.md`（指标扫描）· `g3_fix_verify.md`（准则 c 修复验证）· 及 2019 预测实验相关文档。
