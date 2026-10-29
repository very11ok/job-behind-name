"""反向概率表：从后果出发，看"后果发生的对象中前因成立的比例"。

与 merge_judge.py 的正向表互为贝叶斯逆：
  正向  P(后果 | holds=1)  vs  P(后果 | holds=0)
  反向  P(holds=1 | 后果=1)  vs  P(holds=1 | 后果=0)

反向提升比 = P(holds=1|outcome=1) / P(holds=1|outcome=0)
  >1：后果发生时前因更可能成立（准则有解释力）
  <1：后果发生时前因更不可能成立（反向关系）

输入：out/objects/judge_g{1,2,3}_2020.parquet（LLM 判定，已落库）
      out/objects/labels_g{1,2,3}_2020.parquet（后果标签）
输出：out/results/reverse_outcome_antecedent_2020.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

BASE = Path(r"D:\harness office\research\jobtask-agent")
OUT = BASE / "out"
OBJ = OUT / "objects"
RES = OUT / "results"

RULES = {
    "g1": ("job", "mixed_new"),        # (a) 岗位任务集 → 混合型新组合
    "g2": ("seed", "split"),           # (b) 任务团 → 分裂
    "g3": ("firm", "above_median"),    # (c) 企业 → 模板采纳占比超中位
}


def reverse_table(j: pd.DataFrame, lab: pd.DataFrame, key: str, outcome: str, rule: str) -> pd.DataFrame:
    """按 h 分组，以 outcome 为条件计算 holds 的条件概率。"""
    m = j.merge(lab, on=key, how="inner")
    rows = []
    for h, g in m.groupby("h"):
        a = g[g[outcome] == 1]    # 后果发生
        b = g[g[outcome] == 0]    # 后果未发生
        p1 = a["holds"].mean() if len(a) else float("nan")  # P(holds=1 | outcome=1)
        p0 = b["holds"].mean() if len(b) else float("nan")  # P(holds=1 | outcome=0)
        base = g["holds"].mean()                              # 基础成立率
        rows.append({
            "rule": rule, "h": int(h), "n": len(g),
            "P(holds=1|outcome=1)": round(p1, 4) if pd.notna(p1) else None,
            "P(holds=1|outcome=0)": round(p0, 4) if pd.notna(p0) else None,
            "基础成立率": round(base, 4),
            "反向提升比": round(p1 / p0, 2) if pd.notna(p1) and pd.notna(p0) and p0 > 0 else None,
            "n_outcome1": len(a), "n_outcome0": len(b),
        })
    return pd.DataFrame(rows)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    RES.mkdir(parents=True, exist_ok=True)
    all_tables = []
    for rule, (key, outcome) in RULES.items():
        j_path = OBJ / f"judge_{rule}_2020.parquet"
        if not j_path.exists():
            print(f"[错误] {j_path} 不存在，请先运行 merge_judge.py")
            sys.exit(1)
        j = pd.read_parquet(j_path)
        j[key] = j[key].astype(str)
        lab = pd.read_parquet(OBJ / f"labels_{rule}_2020.parquet")
        lab[key] = lab[key].astype(str)
        t = reverse_table(j, lab, key, outcome, rule)
        all_tables.append(t)
        print(f"\n=== {rule} 反向表 ===")
        print(t.to_string(index=False))

    tt = pd.concat(all_tables)
    lines = [
        "# 三准则「后果→前因」反向概率表（T=2020）",
        "",
        "与正向表互为贝叶斯逆：正向看 P(后果|holds)，反向看 P(holds|后果)。",
        "反向提升比 = P(holds=1|outcome=1) / P(holds=1|outcome=0)。",
        "",
        "判读：",
        "  >1 且远超基础率 → 后果发生时前因更常成立，准则有解释力",
        "  ≈1 且接近基础率 → 前因与后果基本独立，准则无区分力",
        "  <1 → 后果发生时前因更不可能成立，反向关系",
        "",
        "基础率（P(holds=1)）高时需警惕：即使准则无解释力，P(holds=1|outcome=1) 也会被拉高。",
        "真正有信息量的是「反向提升比」和「扣除基础率后的净对应力」。",
        "",
        "## 反向概率表",
        "",
        tt.to_markdown(index=False),
        "",
        "## 正向表对照（提升比）",
        "",
        "| rule | h | 正向提升比 | 反向提升比 | 基础成立率 |",
        "|:-----|---:|----------:|----------:|----------:|",
    ]
    # 附正向提升比对照
    forward = pd.read_csv(RES / "antecedent_outcome_2020.md", sep="|", skiprows=7, engine="python")
    # 简单方式：直接从正向 md 文本提取不太可靠，改为重新计算
    for rule, (key, outcome) in RULES.items():
        j = pd.read_parquet(OBJ / f"judge_{rule}_2020.parquet")
        j[key] = j[key].astype(str)
        lab = pd.read_parquet(OBJ / f"labels_{rule}_2020.parquet")
        lab[key] = lab[key].astype(str)
        m = j.merge(lab, on=key, how="inner")
        for h, g in m.groupby("h"):
            a = g[g["holds"] == 1]
            b = g[g["holds"] == 0]
            p1 = a[outcome].mean() if len(a) else float("nan")
            p0 = b[outcome].mean() if len(b) else float("nan")
            fwd = round(p1 / p0, 2) if pd.notna(p1) and pd.notna(p0) and p0 > 0 else None
            rev = tt[(tt["rule"] == rule) & (tt["h"] == int(h))]["反向提升比"].iloc[0]
            base_rate = round(g["holds"].mean(), 4)
            lines.append(f"| {rule} | {int(h)} | {fwd} | {rev} | {base_rate} |")

    lines.append("")
    md = "\n".join(lines)
    out_path = RES / "reverse_outcome_antecedent_2020.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"\n已写出 {out_path}")


if __name__ == "__main__":
    main()
