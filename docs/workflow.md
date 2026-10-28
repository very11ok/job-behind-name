# 工作流详细说明：三准则「前因→后果」条件概率检验

本文档说明整个流水线每一步做了什么、输入输出是什么、脚本之间如何衔接。
脚本在 `scripts/` 目录下，不含任何数据文件。

---

## 0. 研究设计总览

核心想法：三条再捆绑准则各自给出「前因 → T+h 后果」的可检验预测。
对每个判定单元，先用 LLM 逐对象判前因是否成立（holds=0/1）并给出概率档位 p，
再用 T+1/2/3 年的实测后果标签做条件概率汇总：

- P(后果 | holds=1) — 前因成立的对象中后果出现的比例
- P(后果 | holds=0) — 前因不成立的对象中后果出现的比例
- 提升比 = P(后果|holds=1) / P(后果|holds=0)

提升比 > 1 且前因成立组显著高于不成立组，则该准则获得数据支持。

三条准则的判定单元与对齐键：

| 准则 | 单元 | 对齐键 | 后果标签字段 |
|------|------|--------|-------------|
| (a) 互补性再捆绑 | 岗位任务集 | `job` | `mixed_new` |
| (b) 层级解绑 | 任务团 | `seed` | `split` |
| (c) 模仿性模板扩散 | 企业 | `firm` | `above_median` |

---

## 1. 数据前提

流水线依赖以下外部数据（均不在本仓库中）：

- **任务字典**：每个任务的文本描述、暴露等级（E0-E2）、可编码度（codable）、
  语境嵌入度（ctx）、层级（hierarchy）、功能模块（module）
- **岗位快照**：每年每个岗位包含的任务列表（job → tasks）
- **任务共现网络**：任务间的共现边，用于构建投影层
- **企业面板**：每年每家企业的岗位列表
- **模板相似度**：每个岗位的 struct_sim / xfirm_sim / surf_sim 三个相似度数值

这些数据通过 `jtagent` 包的接口加载（`P.load_jobs`、`P.load_edges`、
`P.build_projection`、`firm_panel.build_firm_year_jobs` 等）。

---

## 2. 第一步：对象池构建 — `scripts/objects.py`

### 做什么

为三条准则分别构建判定对象池：每个对象是后续 LLM 判定和后果标签对齐的最小单元。

### 准则一 g1：岗位任务集

- 来源：某年所有岗位的任务列表（≥2 个任务）
- 每个对象记录：`job`（id）、`tasks`（任务 id 列表）、`e_ord`（各任务暴露等级）、
  `cod`（可编码度）、`ctx`（语境嵌入度）、`mod`（功能模块）、`has_E2`/`has_E0`（初判标记）
- 抽样：随机取 2000 个岗位

### 准则二 g2：任务团

- 来源：任务投影层（共现网络的加权投影）上，以每个任务为种子，
  取其同社区（comm）内权重最高的强邻域（按岗位度排序取前 8 个），
  组成 3-15 个任务的紧密任务团
- 每个对象记录：`seed`（核心任务 id）、`comm`（社区 id）、`tasks`、
  `e_ord`、`cod`、`hier`（层级）、`mod`、`e2_share`（E2 任务占比）、`hier_n`（层级数）
- 去重后随机抽样 2000 个任务团（实际约 1502 个）

### 准则三 g3：企业

- 来源：企业面板中某年的企业 × 岗位结构
- 每个对象记录：`firm`（企业 id）、`n_jobs`（岗位数）、`mean_size`（平均任务集大小）、
  `n_mod`（功能模块数）、`e2_share`（E2 占比）、
  `struct_sim`（与自身既往岗位结构相似度均值）、`xfirm_sim`（跨企业结构相似度均值）、
  `surf_sim`（表面文本相似度均值）
- 模板残留 = `surf_sim - max(struct_sim, xfirm_sim)`，残差越大说明措辞像模板但结构没跟上
- 实际约 307 家企业

### 输出

- `out/objects/g1_jobs_{year}.parquet`
- `out/objects/g2_comm_{year}.parquet`
- `out/objects/g3_firms_{year}.parquet`

---

## 3. 第二步：后果标签 — `scripts/outcomes.py`

### 做什么

为每个对象计算 T+h（h=1/2/3 年）的实测后果标签。
对齐键与对象池一致：g1=job、g2=seed、g3=firm。

### 准则一后果：`mixed_new`

- 定义：该岗位在 T+h 年出现新任务组合，且新组合中同时包含高暴露任务和低暴露任务
- 判定方式：对比 T 年与 T+h 年的任务集，新增任务中既有 E2 又有 E0 的岗位标记为 1

### 准则二后果：`split`

- 定义：该任务团在 T+h 年分裂为 ≥2 个更窄岗位，分别承载团的一部分
- 判定方式：T+h 年的任务团核心任务不再全部共现于同一岗位

### 准则三后果：`above_median`

- 定义：该企业在 T+h 年新增岗位中，模板采纳占比高于同年全网中位数
- 判定方式：逐企业计算新增岗位中模板采纳份额，再按同年中位数二值化

### 输出

- `out/objects/labels_g1_{year}.parquet`（含 h=1/2/3 三行/对象）
- `out/objects/labels_g2_{year}.parquet`
- `out/objects/labels_g3_{year}.parquet`

---

## 4. 第三步：判定输入生成 — `scripts/prep_judge_input.py`

### 做什么

把对象池渲染成 LLM 可读的批次文件：每个文件头部是判定协议（前因定义 + 输出格式），
正文是逐个对象块（每个对象的任务列表、暴露等级、可编码度、语境嵌入度等字段）。

### 判定协议（PROTO）

三条准则各自的协议文本定义前因成立的判定标准：

**准则一**：岗位任务集内同时包含 ① 高暴露可编码任务（E2、codable 高）
和 ② 语境嵌入任务（依赖判断/协调/问责/具身，codable 低、E0/E1）。
两类并存 → holds=1；只有一类或两类都弱 → holds=0。

**准则二**：任务团内任务满足 ① 同层级（hierarchy 高度集中）
② 可编码为主（多数任务规则明确）③ 功能凝聚（模块集中、任务性质均质）。
三点基本满足 → holds=1；层级混杂或大量语境嵌入 → holds=0。

**准则三**：企业岗位结构存在「模板残留」——surf_sim 明显高于 struct_sim 和
xfirm_sim，即措辞像流行模板但任务结构并未真正同构。
残差越大 → 越倾向 holds=1；三个数值接近 → holds=0。

### 批次切分

- 每批最多 60 个对象，不足 60 的尾批单独成文件
- g1（2000 对象）→ 34 批，g2（1502 对象）→ 26 批，g3（307 对象）→ 6 批，共 66 批

### 输出

- `out/judge_input/g1_batch_000.txt` … `g1_batch_033.txt`
- `out/judge_input/g2_batch_000.txt` … `g2_batch_025.txt`
- `out/judge_input/g3_batch_000.txt` … `g3_batch_005.txt`

每个文件格式：
```
【判定协议 · 准则(a) 互补性再捆绑 —— 前因判定】
...协议文本...
【输出】严格 JSON 数组...
[id=J38018 | 岗位任务集 5 任务 | 功能模块数 4]
  t9696 | Develop sales plans... | E2高 | 可编码0.50 语境0.25 | 销售
  ...
[id=J42299 | ...]
  ...
```

---

## 5. 第四步：LLM 前因判定 — 动态工作流

### 做什么

用 ZCode 动态工作流（dynamic workflow）并行调度 66 个子代理，
每个子代理负责一个批次的判定：读批次文件 → 逐对象按协议判定 → 写 JSON 到输出目录。

### 工作流脚本

脚本文件：`scripts/judge_workflow.dwf.ts`（原路径 `.zcode/workflow-drafts/三准则前因判定.dwf.ts`）

### 执行逻辑

**阶段 1：并行判定（66 批）**

- 为每个批次创建一个子代理（`判定员-{batch}`），system prompt 统一设定为
  「组织经济学预测 agent 的前因判定员」，要求严格按协议判定、不编造 id、读不到文件如实说明
- 每个子代理的任务：
  1. 用 Read 工具读取对应批次文件
  2. 逐对象按协议判定三个字段：
     - `holds`：前因是否成立，0 或 1
     - `p`：概率档位，只取 0.05/0.1/0.2/0.3/0.5/0.7/0.9 之一
     - `why`：≤30 字中文依据
  3. 用 Write 工具把严格 JSON 数组写入 `out/judge_output/{batch}.json`
  4. 回复只含一个 JSON 对象：`{"written": N, "first": "...", "last": "..."}`
- 所有批次通过 `Promise.all` 同时发起，失败批次在回调内 try/catch 逐个容错
  （不因单批失败而中断整个工作流）

**阶段 2：补标失败批次**

- 收集阶段 1 中 status ≠ "ok" 的批次
- 为每个失败批次创建补标子代理（`补标员-{batch}`），重新执行同一判定任务
- 补标时提示「上一次判定没有成功落盘，请重新完整执行一遍」
- 补标成功 → 计入 okCount，状态标记为 "ok-retry"

**阶段 3：汇总落盘清单**

- 统计成功批次数、仍失败批次列表
- 生成 markdown 摘要（artifact），列出落盘情况

### 输出

- `out/judge_output/g1_batch_000.json` … `g1_batch_033.json`
- `out/judge_output/g2_batch_000.json` … `g2_batch_025.json`
- `out/judge_output/g3_batch_000.json` … `g3_batch_005.json`

每个 JSON 文件格式：
```json
[
  {"id": "J38018", "holds": 1, "p": 0.3, "why": "含E2可编码与E0语境任务并存"},
  {"id": "J42299", "holds": 0, "p": 0.05, "why": "任务均可编码且同模块"},
  ...
]
```

### 失败处理

- 子代理抛异常或 written=0 → 标记 failed，进入补标阶段
- 补标仍失败 → 在汇总中列出，需人工处理
- 工作流本身不会因单批失败而整体失败

---

## 6. 第五步：条件概率合并 — `scripts/merge_judge.py`

### 做什么

把 LLM 判定结果（holds + p）与后果标签（T+h 实测）合并，
输出「前因→后果」条件概率主表和概率档位校准表。

### 合并逻辑

- 按对齐键 inner join：g1 用 `job`、g2 用 `seed`、g3 用 `firm`
- 判定结果去重：同一 id 只保留首次出现的记录
- id 不在对象池中的判定记录被排除

### 条件概率主表

对每个 h（1/2/3）分组计算：

| 列 | 含义 |
|----|------|
| `n` | 对齐后的对象数 |
| `前因成立率` | holds=1 的对象占比 |
| `P(后果\|holds=1)` | 前因成立组中后果出现的比例 |
| `P(后果\|holds=0)` | 前因不成立组中后果出现的比例 |
| `基础率` | 全体对象后果出现的总比例 |
| `提升比(holds=1/0)` | P(后果\|holds=1) / P(后果\|holds=0) |
| `n1`/`n0` | 两组各自的样本量 |

### 概率档位校准表

对每个 h × p 档位（0.05/0.1/0.2/0.3/0.5/0.7/0.9）分组，
计算该档位下的实际后果率（mean）和样本量（count）。
用于检查 LLM 给出的概率档位是否与实测后果率单调对应——
p 档越高，实际后果率应越高，否则说明 LLM 的校准偏差。

### 输出

- `out/objects/judge_g1_2020.parquet`（逐对象判定落库）
- `out/objects/judge_g2_2020.parquet`
- `out/objects/judge_g3_2020.parquet`
- `out/results/antecedent_outcome_2020.md`（条件概率汇总表，markdown 格式）

---

## 7. 流水线衔接图

```
objects.py          →  g1_jobs / g2_comm / g3_firms parquet
      ↓
outcomes.py         →  labels_g1 / g2 / g3 parquet（T+1/2/3 后果标签）
      ↓
prep_judge_input.py →  judge_input/*.txt（66 批，含判定协议）
      ↓
judge_workflow.dwf.ts →  judge_output/*.json（66 批 LLM 判定）
      ↓
merge_judge.py      →  judge_g* parquet + antecedent_outcome_2020.md
```

对齐键贯穿全程：job / seed / firm。

---

## 8. 复现注意事项

1. 所有脚本硬编码路径为 `D:\harness office\research\jobtask-agent\`，
   迁移到其他环境需修改 `BASE` / `OUT` / `OBJ` 等路径变量
2. `objects.py` 依赖 `jtagent` 包（`pairs`、`attrs`、`firm_panel` 模块），
   该包不在公开仓库中
3. LLM 判定工作流依赖 ZCode 的动态工作流功能（dynamic workflow），
   需在 ZCode 环境中运行
4. 后果标签依赖历史年份的任务网络快照（构建 T+h 对照需要 T 年之后的数据）
5. 概率档位 p 仅 7 档，精度有限；如需更细的校准可扩展档位或改为连续值
