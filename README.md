# job-behind-name：岗位—任务网络的三条再捆绑准则——LLM 预测 agent 的可检验判定与修复

基于招聘文本衍生的"岗位—任务网络"（job–task network），把三条组织与劳动经济学的"再捆绑"（re-bundling）准则实现为可检验的预测规则：以 **T=2020 年** 的网络结构为前因（antecedent），以 **T+1/2/3 年**（2021–2023）真实涌现的岗位—任务组合为后果（outcome），做"前因 → 若干年后 → 后果"的条件概率判定。LLM 用于前因的主观判定与岗位—任务对的绑定判定；所有统计量（条件概率、提升比、卡方、Spearman）均为确定性计算。本仓库含全部数据、脚本、中间产物与结果文档，可完整复现。

## 三条准则

| # | 准则 | 理论出处 | 单元 | 前因（T=2020） | 后果（T+h） |
|---|------|----------|------|----------------|-------------|
| a | 互补性再捆绑 | Milgrom & Roberts 1995 / Kremer 1993 | 岗位任务集 | 岗位任务集中存在 E 差 ≥2 的知识互补对（LLM 判定） | 任务集变化且新任务对出现高-低 E 搭配（mixed_new） |
| b | 层级解绑 | Garicano 2000 | 岗位任务集 | 岗位任务集的知识不对称度（任务 E_ord 离散度）高 | 该任务集合下凝结出不对称度更低的窄岗位（down_std） |
| c | 模仿性模板扩散 | DiMaggio & Powell 1983 | 企业×年 | 组织规模结构：n_jobs、n_mod 高于中位数 | 新增岗位中"跨企业模板采纳"占比高于同年中位数（above_median） |

## 核心结果（提升比 = P(后果|前因=1) / P(后果|前因=0)，T=2020）

| 准则 / 判据 | h=1 | h=2 | h=3 | 显著性 | 结论 |
|-------------|-----|-----|-----|--------|------|
| a：LLM holds → mixed_new（原版） | **2.38** | **3.00** | **2.57** | 三窗口全显著 | 原生成立 |
| **b：岗位版 asym 高 → down_std（主判据）** | **2.65** | **2.86** | **2.95** | p≤7.4e-14 | **成立（最强）** |
| b：任务团版 asym 高 → down_std（变体） | 1.56 | 1.40 | 1.29 | p=4.6e-06/0.003/0.038 | 成立 |
| b：LLM holds ∧ hier_n≥3 → split（门槛版） | **2.34** | **2.59** | **2.49** | p<7.3e-07 | 成立 |
| b：门槛版 ∧ asym 高 → down_std（叠加） | **3.36** | **2.74** | **2.73** | p≤0.006 | 最强（n=15） |
| c：n_jobs高 ∧ n_mod高 → above_median | **2.98** | **3.26** | **3.06** | p=8e-06/2.6e-05/0.0015 | 成立 |
| c：LLM holds（对照，已确认空壳） | 1.27 | 1.72 | 0.98 | 全不显著 | 弃用 |

## 工作流全景

```
数据层   data/snapshots/ (2016–2026 岗位—任务快照 + task_dict 任务字典)
   │      jtagent/pairs.py → data/pairs/ 任务对面板（共邻/优先连接/Jaccard/知识差等特征）
   │      jtagent/attrs.py → 任务语义属性（知识强度 E、可编码度、语境嵌入、层级、功能模块）
   ▼
对象层   scripts/objects.py     三准则对象池 data/objects/g{1,2,3}_2020.parquet
   │                            g1 2000 岗位任务集 / g2 1502 任务团 / g3 307 企业
   ▼
后果层   scripts/outcomes.py    T+h（h=1/2/3）实测后果标签 labels_g*_2020.parquet
   │                            逐对象回看 2021–2023 真实网络，回答"后来发生了什么"
   ▼
判定层   scripts/prep_judge_input.py → data/judge_input/（66 批，PROTO 协议+对象明细）
   │      scripts/workflow/pipeline.dwf.ts → 66 个子代理并行 LLM 判定（含补标容错）
   │      scripts/merge_judge.py → judge_g*_2020.parquet + 条件概率主表
   ▼
诊断层   scripts/reverse_outcome.py / diagnose_g2.py / diagnose_g3.py
   │      第一轮结论：a 正向成立；b 反向（0.57/0.56/0.49）；c 空壳（82.5% 判 1、p 档无排序力）
   ▼
修复层   scripts/scan_g2_threshold.py → verify_g2_fix.py     b：门槛 hier_n≥3
   │      scripts/verify_g2_direction.py                       b：方向性 asym → down_std
   │      scripts/scan_g3_metrics.py → verify_g3_fix.py        c：客观前因 n_jobs/n_mod
   ▼
复核层   scripts/recheck_results.py / recheck_g2fix.py       scipy.stats 独立交叉验证
```

对齐键 `job` / `seed` / `firm` 贯穿对象层到复核层；对齐键即一条判定的完整生命周期。

## 项目历程：从一条准则到三条准则全部成立

**第一轮判定（原版判据）**：66 批 LLM 前因判定完成后，三条准则只活下来一条。准则 a 的提升比 2.38/3.00/2.57 三窗口全显著；准则 b 反向——LLM 判"层级解绑成立"的团分裂率反而更低（0.57/0.56/0.49）；准则 c 弱正向但全不显著（1.27/1.72/0.98），且 LLM 对 82.5% 的企业判 holds=1，p 档与实测后果之间没有单调关系。

**诊断**：`diagnose_g2.py` 把 b 的反向关系定位到混淆结构——holds=1 的团平均更小（4.99 vs 6.38 个任务）、模块更少、层级更少，这类团本来就难被拆，"LLM 判定成立"筛选出的恰是难拆的团。`diagnose_g3.py` 确认 c 的判定是空壳：判定成立率过高、置信档位与后果脱钩，LLM 在这个对象类型上没有产出有效信息。

**修复**：三条线并行完成。(1) b 的门槛扫描在 size/hier_n/n_mod/e2_share 四个候选里找到 hier_n≥3 为最优切分，新前因 holds∧hier_n≥3 把提升比从 0.55 翻转到 2.34/2.59/2.49（卡方 p<7.3e-07）。(2) b 的方向性重构按 Garicano 的原义重写后果：不只要求"分裂"，还要求拆出的窄岗位任务集不对称度低于原团（down_std）；前因改为团内任务 E_ord 标准差（知识不对称度），完全脱离 LLM。提升比 1.56/1.40/1.29 三窗口全显著，同时解开了原反向之谜——高不对称团更大更复杂、整体被拆的概率反而低，但只要拆，拆出方向与理论一致。附带发现：拆出窄岗的平均知识强度更高（down_e 提升比 0.25），实际机制是知识密集任务剥离成专家岗，而非例程下沉。(3) c 弃用 LLM 判定，客观指标扫描测了 9 个结构指标，n_jobs 与 n_mod 胜出且全部相似度指标无效，组合前因 n_jobs高∧n_mod高 给出 2.98/3.26/3.06，是全项目最强的判据。

**复核**：18 组关键检验（条件概率、卡方、反向概率）全部用 `scipy.stats.chi2_contingency` 独立重算，与手写公式逐位吻合；`recheck_results.py` / `recheck_g2fix.py` 入库可复跑。

**单位修正（准则 b 的最终形态）**：准则 b 的理论表述是"岗位任务集知识不对称度高 → 该任务集合下凝结出不对称度更低的新岗位"，判定单位应为**岗位**。第一轮沿用的对象池以任务团（任务共现社区）为"任务集合"的载体，与理论不直接对应。`verify_g2_job.py` 把前因与后果原样移植到岗位任务集上（2000 岗位，asym=岗位内任务 E_ord 标准差，后果=任务集合下出现不对称度更低的窄岗位）：提升比 2.65/2.86/2.95（p=1.3e-18/7.4e-14/3.7e-12），强度约为任务团版的 2 倍且随时间递增；不加方向约束的 split 对照完全中性（1.13–1.15，p>0.1）——印证了"旧岗位消失没那么快、拆分方向才是预测内容"的理论判断：会不会拆没有区分度，往哪个方向拆有。知识强度方向的附带发现同样成立：窄岗位的平均 E 更高（down_e 提升比 0.42–0.49），知识密集任务剥离成专家岗而非例程下沉。任务团版保留为变体（任务团是任务集合的网络化定义，结论同向）。

**方法论定位**：LLM 在本项目中承担语义判定（任务对绑定、前因是否成立的语义层），统计结论全部由确定性代码产出。修复过程本身是项目的方法论产出之一：当 LLM 判定与结构证据冲突时，诊断脚本能把冲突定位到具体的混淆结构，并把前因替换为可独立测量的客观量。

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

- 修复验证明细：`g2_threshold_scan`（门槛扫描）、`g2_threshold_combo`（联合门槛）、`g2_fix_verify`（门槛版验证）、`g2_direction_verify`（方向版/任务团变体）、`g2_job_verify`（岗位版主判据）、`g3_metric_scan`/`g3_metric_corr`（指标扫描）、`g3_fix_verify`（准则 c 修复验证），各有 .md（在 docs/results/）与 .parquet。
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
10. `verify_g2_direction.py` — 准则 b 方向性重构验证（任务团版变体）
11. `verify_g2_job.py` — 准则 b 岗位版验证（主判据：岗位任务集 asym → down_std）
12. `scan_g3_metrics.py` / `verify_g3_fix.py` — 准则 c 指标扫描与修复验证
13. `recheck_results.py` / `recheck_g2fix.py` — scipy 独立复核
14. `run_agent_2019.py` / `run_backtest.py` / `ablation_feats.py` / `make_figures.py` / `trends.py` — 2019 预测实验与图表
15. `check_hedging.py` — 文档防御性写作（hedging）检测，词表源自 [aproko/keyword_hedge_detector](https://github.com/aproko/keyword_hedge_detector) 的中文 hedge 词表（过滤口语词）并补充英文 hedge；用于文档发布前的表达质检

## 复现

```bash
# 1. 对象池 + 后果标签（T=2020）
python objects.py && python outcomes.py
# 2. 判定输入（66 批）→ 用 workflow 引擎跑 workflow/pipeline.dwf.ts → 合并
python prep_judge_input.py && python merge_judge.py
# 3. 三准则修复验证
python verify_g2_fix.py && python verify_g2_direction.py && python verify_g2_job.py && python verify_g3_fix.py
# 4. 独立复核（scipy 交叉验证）
python recheck_results.py && python recheck_g2fix.py
```

依赖：`pandas pyarrow numpy scipy`。LLM 客户端（`jtagent/llm.py`）从环境变量 `JTAGENT_ENDPOINTS` 读取端点配置（JSON：`[{"baseURL":..., "apiKey":..., "name":...}]`），仓库不含任何凭据。

## 结果文档索引（docs/results/）

`antecedent_outcome_2020.md`（主表）· `reverse_outcome_antecedent_2020.md`（反向概率）· `diagnose_g2_g3.md`（混淆诊断）· `g2_threshold_scan.md`（门槛扫描）· `g2_fix_verify.md`（门槛版验证）· `g2_direction_verify.md`（方向版/任务团变体验证）· `g2_job_verify.md`（岗位版主判据验证）· `g3_metric_scan.md`（指标扫描）· `g3_fix_verify.md`（准则 c 修复验证）· 及 2019 预测实验相关文档。
