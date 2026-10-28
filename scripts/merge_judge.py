"""合并 LLM 前因判定与后果标签，输出"前因→后果"条件概率表。

输入：out/judge_output/{g1,g2,g3}_batch_*.json（LLM 判定）
      out/objects/labels_g{1,2,3}_2020.parquet（后果标签）
输出：out/objects/judge_g{1,2,3}_2020.parquet（逐对象判定落库）
      out/results/antecedent_outcome_2020.md（条件概率汇总表）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

BASE = Path(r"D:\harness office\research\jobtask-agent")
OUT = BASE / "out"
JD = OUT / "judge_output"
OBJ = OUT / "objects"
RES = OUT / "results"

RULES = {
    "g1": ("job", "mixed_new"),        # (a) 岗位任务集 → 混合型新组合
    "g2": ("seed", "split"),           # (b) 任务团 → 分裂
    "g3": ("firm", "above_median"),    # (c) 企业 → 模板采纳占比超中位
}


def load_judgments(rule: str) -> pd.DataFrame:
    files = sorted(JD.glob(f"{rule}_batch_*.json"))
    if not files:
        raise FileNotFoundError(f"{rule} 无判定文件")
    rows = []
    for f in files:
        try:
            arr = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  [跳过] {f.name} JSON 解析失败: {e}")
            continue
        if not isinstance(arr, list):
            print(f"  [跳过] {f.name} 不是 JSON 数组")
            continue
        for x in arr:
            if not isinstance(x, dict) or "id" not in x:
                continue
            rows.append({
                rule: str(x["id"]),
                "holds": int(x.get("holds", 0) in (1, "1", True)),
                "p": float(x.get("p", 0.0)),
                "why": str(x.get("why", ""))[:60],
                "batch": f.stem,
            })
    df = pd.DataFrame(rows).drop_duplicates(subset=[rule], keep="first")
    return df


def cond_table(j: pd.DataFrame, lab: pd.DataFrame, key: str, outcome: str, rule: str) -> pd.DataFrame:
    m = j.merge(lab, on=key, how="inner")
    rows = []
    for h, g in m.groupby("h"):
        a = g[g["holds"] == 1]
        b = g[g["holds"] == 0]
        base = g[outcome].mean()
        p1 = a[outcome].mean() if len(a) else float("nan")
        p0 = b[outcome].mean() if len(b) else float("nan")
        rows.append({
            "rule": rule, "h": int(h), "n": len(g),
            "前因成立率": round(g["holds"].mean(), 4),
            "P(后果|holds=1)": round(p1, 4) if pd.notna(p1) else None,
            "P(后果|holds=0)": round(p0, 4) if pd.notna(p0) else None,
            "基础率": round(base, 4),
            "提升比(holds=1/0)": round(p1 / p0, 2) if pd.notna(p1) and pd.notna(p0) and p0 > 0 else None,
            "n1": len(a), "n0": len(b),
        })
    return pd.DataFrame(rows)


def calib_table(j: pd.DataFrame, lab: pd.DataFrame, key: str, outcome: str) -> pd.DataFrame:
    m = j.merge(lab, on=key, how="inner")
    m["p档"] = m["p"].map({0.05: "0.05", 0.1: "0.1", 0.2: "0.2", 0.3: "0.3",
                           0.5: "0.5", 0.7: "0.7", 0.9: "0.9"}).fillna(m["p"].round(2).astype(str))
    return (m.groupby(["h", "p档"])[outcome]
            .agg(["mean", "count"]).rename(columns={"mean": "实际后果率", "count": "n"})
            .round(4).reset_index())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    RES.mkdir(parents=True, exist_ok=True)
    all_tables, all_calib = [], []
    for rule, (key, outcome) in RULES.items():
        j = load_judgments(rule)
        pool = pd.read_parquet(OBJ / f"{rule}_{'jobs' if rule=='g1' else 'comm' if rule=='g2' else 'firms'}_{2020}.parquet")
        known = set(pool[key].astype(str))
        miss = len(j) - j[key].isin(known).sum()
        j.to_parquet(OBJ / f"judge_{rule}_2020.parquet", index=False)
        lab = pd.read_parquet(OBJ / f"labels_{rule}_2020.parquet")
        lab[key] = lab[key].astype(str)
        t = cond_table(j, lab, key, outcome, rule)
        all_tables.append(t)
        c = calib_table(j, lab, key, outcome)
        c.insert(0, "rule", rule)
        all_calib.append(c)
        n_merged = j.merge(lab, on=key, how="inner").shape[0]
        print(f"\n=== {rule}（判定 {len(j)} 对象，其中 id 不在池中 {miss}；判定与标签对齐后 {n_merged}）===")
        print(t.to_string(index=False))

    tt = pd.concat(all_tables)
    cc = pd.concat(all_calib)
    lines = ["# 三准则「前因→若干年后→后果」条件概率表（T=2020）", ""]
    lines.append("判定来源：LLM 逐对象前因判定（out/judge_output/）；后果：labels_g*_2020（T+h 实测）。")
    lines.append("P(后果|holds=1) 显著高于 P(后果|holds=0) 且提升比 > 1，即该准则获得支持。")
    lines.append("")
    lines.append("## 条件概率主表")
    lines.append("")
    lines.append(tt.to_markdown(index=False))
    lines.append("")
    lines.append("## 概率档位校准表（LLM 的 p 档 vs 实际后果率）")
    lines.append("")
    lines.append(cc.to_markdown(index=False))
    md = "\n".join(lines)
    (RES / "antecedent_outcome_2020.md").write_text(md, encoding="utf-8")
    print(f"\n已写出 {RES / 'antecedent_outcome_2020.md'}")


if __name__ == "__main__":
    main()
