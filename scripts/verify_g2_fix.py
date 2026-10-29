"""g2 修复验证：在新前因定义（holds ∧ hier_n>=3）下跑条件概率，
分别看 h=1, 2, 3 三个时间窗口。"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

BASE = Path(r"D:\harness office\research\jobtask-agent")
OUT = BASE / "out"
OBJ = OUT / "objects"
RES = OUT / "results"


def merge_g2() -> pd.DataFrame:
    j = pd.read_parquet(OBJ / "judge_g2_2020.parquet")
    comm = pd.read_parquet(OBJ / "g2_comm_2020.parquet")
    lab = pd.read_parquet(OBJ / "labels_g2_2020.parquet")
    for df in [j, comm, lab]:
        df["seed"] = df["seed"].astype(str)
    m = j.merge(comm[["seed", "size", "n_mod", "e2_share", "hier_n"]],
                on="seed", how="inner")
    m = m.merge(lab[["seed", "h", "split"]], on="seed", how="inner")
    return m


def cond_table(m: pd.DataFrame, holds_col: str, label: str) -> pd.DataFrame:
    rows = []
    for h, g in m.groupby("h"):
        a = g[g[holds_col] == 1]
        b = g[g[holds_col] == 0]
        p1 = a["split"].mean() if len(a) else float("nan")
        p0 = b["split"].mean() if len(b) else float("nan")
        lift = p1 / p0 if pd.notna(p1) and pd.notna(p0) and p0 > 0 else float("nan")
        rows.append({
            "定义": label, "h": int(h), "n": len(g),
            "n1": len(a), "n0": len(b),
            "P(split|holds=1)": round(p1, 4) if pd.notna(p1) else None,
            "P(split|holds=0)": round(p0, 4) if pd.notna(p0) else None,
            "基础率": round(g["split"].mean(), 4),
            "提升比": round(lift, 2) if pd.notna(lift) else None,
        })
    return pd.DataFrame(rows)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    m = merge_g2()

    # 新前因定义：holds ∧ hier_n >= 3
    m["holds_new"] = (m["holds"] == 1) & (m["hier_n"] >= 3)
    m["holds_new"] = m["holds_new"].astype(int)

    tables = []
    # 原定义
    tables.append(cond_table(m, "holds", "原: holds"))
    # 新定义：hier_n >= 3
    tables.append(cond_table(m, "holds_new", "新: holds ∧ hier_n≥3"))

    # 对比表
    for t in tables:
        print(t.to_string(index=False))
        print()

    tt = pd.concat(tables)

    # 反向概率对比
    print("=== 反向概率对比 ===")
    rev_rows = []
    for label, col in [("原: holds", "holds"), ("新: holds ∧ hier_n≥3", "holds_new")]:
        for h, g in m.groupby("h"):
            s1 = g[g["split"] == 1][col]
            s0 = g[g["split"] == 0][col]
            p1 = s1.mean() if len(s1) else float("nan")
            p0 = s0.mean() if len(s0) else float("nan")
            rev_lift = p1 / p0 if pd.notna(p1) and pd.notna(p0) and p0 > 0 else float("nan")
            rev_rows.append({
                "定义": label, "h": int(h),
                "P(holds=1|split=1)": round(p1, 4) if pd.notna(p1) else None,
                "P(holds=1|split=0)": round(p0, 4) if pd.notna(p0) else None,
                "反向提升比": round(rev_lift, 2) if pd.notna(rev_lift) else None,
            })
    rev = pd.DataFrame(rev_rows)
    print(rev.to_string(index=False))

    # 写 markdown
    RES.mkdir(parents=True, exist_ok=True)
    lines = ["# g2 修复验证：新前因定义（holds ∧ hier_n≥3）", ""]
    lines.append("门槛来源：门槛扫描发现 hier_n≥3 时反向关系消失，提升比从 0.55 跳到 1.68。")
    lines.append("")
    lines.append("## 条件概率对比（按时间窗口 h）")
    lines.append("")
    lines.append(tt.to_markdown(index=False))
    lines.append("")
    lines.append("## 反向概率对比")
    lines.append("")
    lines.append(rev.to_markdown(index=False))
    lines.append("")

    # 卡方检验
    lines.append("## 卡方独立性检验")
    lines.append("")
    for label, col in [("原: holds", "holds"), ("新: holds ∧ hier_n≥3", "holds_new")]:
        for h, g in m.groupby("h"):
            ct = pd.crosstab(g[col], g["split"])
            if ct.shape == (2, 2):
                n = len(g)
                a, b = ct.iloc[0, 0], ct.iloc[0, 1]
                c, d = ct.iloc[1, 0], ct.iloc[1, 1]
                chi2 = (a * d - b * c) ** 2 * n / (
                    (a + b) * (c + d) * (a + c) * (b + d)
                )
                lines.append(f"- {label}, h={int(h)}: χ²={chi2:.2f}, n={n}")
    lines.append("")

    md = "\n".join(lines)
    (RES / "g2_fix_verify.md").write_text(md, encoding="utf-8")
    print(f"\n已写出 {RES / 'g2_fix_verify.md'}")


if __name__ == "__main__":
    main()
