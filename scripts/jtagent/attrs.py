"""任务属性表：暴露等级、语境嵌入度、可编码度、职业模块。

语境嵌入度 / 可编码度 = 词表法（O*NET 英文任务陈述），与暴露等级正交，
避免与 (a) 规则的 E_gap 项循环。词表分四类：判断 / 协调 / 问责 / 具身情境。
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

OUT = Path(r"D:\harness office\research\jobtask-agent\out")

_LEX = {
    "judgment": [r"judge", r"judgment", r"assess\b", r"evaluat", r"determine\b",
                 r"decid", r"apprais", r"interpret", r"diagnos", r"troubleshoot",
                 r"resolve\b", r"recommend", r"advis", r"counsel", r"prioriti",
                 r"discretion", r"analy[sz]e", r"plan\b", r"strateg", r"forecast",
                 r"\bdesign\b", r"develop\b"],
    "coordination": [r"coordinat", r"collaborat", r"liais", r"negotiat", r"consult",
                     r"communicat", r"confer\b", r"facilitat", r"mediat", r"supervis",
                     r"oversee", r"direct\b", r"delegate", r"mentor", r"train\b",
                     r"coach", r"interact", r"customer", r"client", r"vendor",
                     r"supplier", r"\bteam\b", r"personnel", r"staff\b", r"interview"],
    "accountability": [r"approv", r"authoriz", r"certif", r"ensur", r"accountab",
                       r"responsib", r"audit", r"review\b", r"enforc", r"verif",
                       r"inspect", r"complianc", r"legal", r"safety", r"quality\b",
                       r"standard\b", r"policy\b", r"guidelin"],
    "embodied": [r"operat", r"install", r"repair", r"maintain\b", r"clean\b",
                 r"physic", r"manual", r"hands?-?on", r"on[- ]site", r"field\b",
                 r"travel", r"equipment\b", r"machin", r"tool", r"laborator",
                 r"specimen", r"sample\b", r"wear\b", r"lift\b", r"pack"],
}
_COD = [r"\benter\b", r"\bentering\b", r"record\b", r"compil", r"calculat",
        r"\bcompute", r"transcrib", r"schedul", r"\bfile\b", r"filing",
        r"tabulat", r"bookkeep", r"proofread", r"translat", r"\bcode\b",
        r"\bcoding\b", r"typ(e|ing)\b", r"data[- ]entry", r"prepare.{0,20}(report|correspond|document|form)",
        r"(write|draft|edit).{0,30}(report|correspond|memo|email|document)",
        r"(maintain|update).{0,20}(record|database|file|log)", r"process.{0,15}(data|form|paperwork|application)",
        r"summariz", r"sort\b", r"check.{0,20}(accuracy|error|completeness)"]


def _count_hits(text: str, patterns: list[str]) -> int:
    return sum(1 for p in patterns if re.search(p, text, flags=re.IGNORECASE))


def build_task_attrs(task_dict: pd.DataFrame) -> pd.DataFrame:
    """task_dict: task, task_text, soc, occupation, E, E_ord -> 追加 ctx/cod/module 列。"""
    df = task_dict.copy()
    txt = df["task_text"].fillna("").astype(str)
    for cat, pats in _LEX.items():
        df[f"lex_{cat}"] = txt.map(lambda s, p=pats: _count_hits(s, p))
    df["lex_codable"] = txt.map(lambda s: _count_hits(s, _COD))

    df["ctx_raw"] = df[["lex_judgment", "lex_coordination",
                        "lex_accountability", "lex_embodied"]].clip(0, 1).sum(axis=1)
    # 语境嵌入度 ∈ [0,1]：命中类别数 / 4
    df["ctx"] = df["ctx_raw"] / 4.0
    # 可编码度 ∈ [0,1]
    df["codable"] = df["lex_codable"].clip(0, 2) / 2.0
    # 职业模块 = O*NET SOC 前三位（major group 级）
    df["module"] = df["soc"].fillna("").astype(str).str[:4]
    return df


def add_degree(attrs: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    """把该年度任务度（连接岗位数）并进属性表。"""
    deg = edges.groupby("task")["job"].nunique().rename("deg")
    df = attrs.merge(deg, on="task", how="left")
    df["deg"] = df["deg"].fillna(0).astype(int)
    return df


def load_attrs(out: Path = OUT, mode: str = "merge") -> pd.DataFrame:
    """任务属性。mode:
      lex   = 仅词表（消融基线）
      llm   = 仅 LLM 标注（未标注任务置 NaN）
      merge = LLM 优先、词表回填（默认）
    LLM 标注来源 out/results/anno_*.parquet（多批可合并；判断/协调/问责/具身四个 0/1
    的均值作为 ctx_llm；codability/2 作为 codable_llm；hierarchy、module 取首个标注者）。
    """
    td = pd.read_parquet(out / "snapshots" / "task_dict.parquet")
    df = build_task_attrs(td)
    if mode == "lex":
        df["attr_src"] = "lex"
        return df

    annos = []
    res_dir = out / "results"
    if res_dir.exists():
        for f in sorted(res_dir.glob("anno_*.parquet")):
            annos.append(pd.read_parquet(f))
    if annos:
        a = pd.concat(annos).drop_duplicates("id").rename(columns={"id": "task"})
        a["ctx_llm"] = a[["judgment", "coordination", "accountability", "embodied"]].mean(axis=1)
        a["codable_llm"] = pd.to_numeric(a["codability"], errors="coerce") / 2.0
        a = a[["task", "ctx_llm", "codable_llm", "hierarchy", "module"]].rename(columns={"module": "module_llm"})
        df = df.merge(a, on="task", how="left")
    else:
        df["ctx_llm"] = np.nan
        df["codable_llm"] = np.nan
        df["module_llm"] = pd.Series(dtype=object)
        df["hierarchy"] = pd.Series(dtype=object)

    df["attr_src"] = "lex"
    if mode in ("merge", "llm"):
        has = df["ctx_llm"].notna()
        df.loc[has, "attr_src"] = "llm"
        if mode == "merge":
            df["ctx"] = df["ctx_llm"].where(has, df["ctx"])
            df["codable"] = df["codable_llm"].where(has, df["codable"])
            df["module"] = df["module_llm"].where(has, df["module"])
        else:
            df["ctx"] = df["ctx_llm"]
            df["codable"] = df["codable_llm"]
            df["module"] = df["module_llm"]
    return df
