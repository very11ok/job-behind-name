"""让 LLM 逐个对象判前因 + 概率档位。三份提示词对应三条准则。

输出 JSON 每对象一行：
  g1: {"job": "...", "prior": <0|1>, "p": <0..1>, "level": <"低"|"中"|"高">, "why": "..."}
  g2: {"seed": <int>, "prior": ..., "p": ..., "level": ..., "why": ...}
  g3: {"firm": "...", "prior": ..., "p": ..., "level": ..., "why": ...}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
OUT = Path(r"D:\harness office\research\jobtask-agent\out")

SYS_G1 = """你是组织经济学判定器。给你一个岗位的任务集合（每条任务带：O*NET任务原文、
GPT-4暴露等级E0/E1/E2、可编码性cod 0-2、语境嵌入ctx 0-1、功能模块）。

【准则 (a) 互补性再捆绑】AI 吸收可编码任务后，剩余的难吸收任务（判断/协调/问责/具身）
与被吸收的高暴露任务重新捆绑。
前因 = 该岗位任务集内**同时存在**：可被AI吸收的高暴露可编码任务 + 难以吸收的语境嵌入任务。

请判断该岗位是否具备这一前因，并预测其未来是否演化为"混合型新组合"（任务集出现
高暴露×低暴露的新搭配）。输出一行 JSON：
{"job": "<岗位id>", "prior": <1=具备前因 0=不具备>, "p": <0..1 出现混合型新组合的概率>,
 "level": "<低|中|高>", "why": "<≤25字，指认前因依据>"}
只依据给定信息，strict JSON 数组输出。"""

SYS_G2 = """你是组织经济学判定器。给你一个"任务团"（投影网络中紧密相连的一组任务，
每条带暴露等级E、可编码性cod、知识层级L0-L3、功能模块）。

【准则 (b) 层级解绑】知识获取成本下降后，问题解决跨度缩小，同一知识层级的可编码任务
被拆进更狭窄、更均质的岗位。
前因 = 团内任务**同层级、可编码、功能同质**（即是一块可被整齐切下的知识模块）。

请判断该团是否具备前因，并预测其未来是否**分裂**为若干更窄的新任务集。输出一行 JSON：
{"seed": <int 种子任务id>, "prior": <1|0>, "p": <0..1 发生分裂的概率>,
 "level": "<低|中|高>", "why": "<≤25字>"}
strict JSON 数组输出。"""

SYS_G3 = """你是组织经济学判定器。给你一个企业在该年的岗位结构摘要
（岗位数、平均任务数、任务功能模块分布、跨企业模板采纳率、暴露结构）。

【准则 (c) 模仿性模板扩散】不确定条件下组织复制看似成功的结构。
前因 = 该企业结构中**已存在跨企业模板烙印**（其岗位组合与外部模板高度同构）。

请判断该企业是否具备前因，并预测未来其新增岗位中模板采纳比例是否高于行业同期。
输出一行 JSON：
{"firm": "<企业代码>", "prior": <1|0>, "p": <0..1>, "level": "<低|中|高>", "why": "<≤25字>"}
strict JSON 数组输出。"""


def prep_batches(rule: str, year: int = 2020, batch: int = 40) -> list[Path]:
    """把对象池切成 LLM 输入批次（CSV）。"""
    d_in = OUT / "prior_in" / rule / str(year)
    d_in.mkdir(parents=True, exist_ok=True)
    if rule == "g1":
        df = pd.read_parquet(OUT / "objects" / f"g1_jobs_{year}.parquet")
        cols = ["job", "size", "e_ord", "cod", "ctx", "mod"]
    elif rule == "g2":
        df = pd.read_parquet(OUT / "objects" / f"g2_comm_{year}.parquet")
        cols = ["seed", "size", "e_ord", "cod", "hier", "mod"]
    else:
        p = OUT / "objects" / f"g3_firms_{year}.parquet"
        df = pd.read_parquet(p)
        cols = list(df.columns)
    df = df[cols].reset_index(drop=True)
    paths = []
    for k in range(0, len(df), batch):
        f = d_in / f"batch_{k//batch:03d}.csv"
        df.iloc[k:k + batch].to_csv(f, index=False, encoding="utf-8-sig")
        paths.append(f)
    (d_in / "meta.json").write_text(json.dumps(
        {"rule": rule, "year": year, "n": len(df), "batches": len(paths)}, ensure_ascii=False), "utf-8")
    print(f"[{rule}] {len(df)} 对象 → {len(paths)} 批")
    return paths


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for r in sys.argv[1:] or ["g1", "g2"]:
        prep_batches(r, 2020)