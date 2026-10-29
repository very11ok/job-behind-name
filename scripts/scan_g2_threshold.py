"""g2 门槛扫描：寻找使反向关系消失或变正向的 size/hier_n 切分点。

诊断发现 g2 反向关系是混淆变量驱动的——LLM 把前因成立判给小型简单团，
真正分裂的是大型复杂团。本脚本扫描 size 和 hier_n 的门槛值，
在每个门槛下计算条件概率，找使 P(split|holds=1) >= P(split|holds=0) 的切分点。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

BASE = Path(r"D:\harness office\research\jobtask-agent")
OUT = BASE / "out"
OBJ = OUT / "objects"
RES = OUT / "results"


def merge_g2() -> pd.DataFrame:
    """合并判定、团特征、后果标签。"""
    j = pd.read_parquet(OBJ / "judge_g2_2020.parquet")
    comm = pd.read_parquet(OBJ / "g2_comm_2020.parquet")
    lab = pd.read_parquet(OBJ / "labels_g2_2020.parquet")

    j["seed"] = j["seed"].astype(str)
    comm["seed"] = comm["seed"].astype(str)
    lab["seed"] = lab["seed"].astype(str)

    m = j.merge(comm[["seed", "size", "n_mod", "e2_share", "hier_n", "mod"]],
                on="seed", how="inner")
    m = m.merge(lab[["seed", "split"]], on="seed", how="inner")
    return m


def cond_at_threshold(m: pd.DataFrame, col: str, threshold: int) -> dict:
    """在指定门槛下计算条件概率。"""
    sub = m[m[col] >= threshold]
    n = len(sub)
    if n < 20:
        return {"threshold": threshold, "n": n, "valid": False}

    h1 = sub[sub["holds"] == 1]
    h0 = sub[sub["holds"] == 0]
    p1 = h1["split"].mean() if len(h1) else float("nan")
    p0 = h0["split"].mean() if len(h0) else float("nan")
    lift = p1 / p0 if pd.notna(p1) and pd.notna(p0) and p0 > 0 else float("nan")

    return {
        "threshold": threshold,
        "n": n,
        "n_h1": len(h1),
        "n_h0": len(h0),
        "P(split|holds=1)": round(p1, 4) if pd.notna(p1) else None,
        "P(split|holds=0)": round(p0, 4) if pd.notna(p0) else None,
        "提升比": round(lift, 2) if pd.notna(lift) else None,
        "valid": True,
    }


def scan_thresholds(m: pd.DataFrame) -> pd.DataFrame:
    """扫描 size 和 hier_n 的多个门槛值。"""
    rows = []

    # size 门槛扫描
    for th in [1, 3, 5, 7, 9, 11, 13, 15, 20, 25]:
        r = cond_at_threshold(m, "size", th)
        r["变量"] = "size"
        rows.append(r)

    # hier_n 门槛扫描
    for th in [1, 2, 3, 4, 5, 6]:
        r = cond_at_threshold(m, "hier_n", th)
        r["变量"] = "hier_n"
        rows.append(r)

    return pd.DataFrame(rows)


def scan_combined(m: pd.DataFrame) -> pd.DataFrame:
    """扫描 size 和 hier_n 的联合门槛。"""
    rows = []
    for s_th in [3, 5, 7, 9, 11]:
        for h_th in [2, 3, 4]:
            sub = m[(m["size"] >= s_th) & (m["hier_n"] >= h_th)]
            n = len(sub)
            if n < 20:
                continue
            h1 = sub[sub["holds"] == 1]
            h0 = sub[sub["holds"] == 0]
            p1 = h1["split"].mean() if len(h1) else float("nan")
            p0 = h0["split"].mean() if len(h0) else float("nan")
            lift = p1 / p0 if pd.notna(p1) and pd.notna(p0) and p0 > 0 else float("nan")
            rows.append({
                "size门槛": s_th,
                "hier_n门槛": h_th,
                "n": n,
                "n_h1": len(h1),
                "n_h0": len(h0),
                "P(split|holds=1)": round(p1, 4) if pd.notna(p1) else None,
                "P(split|holds=0)": round(p0, 4) if pd.notna(p0) else None,
                "提升比": round(lift, 2) if pd.notna(lift) else None,
            })
    return pd.DataFrame(rows)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    m = merge_g2()

    print(f"总样本: {len(m)}")
    print(f"holds=1: {len(m[m['holds']==1])}, holds=0: {len(m[m['holds']==0])}")
    print(f"split 基础率: {m['split'].mean():.4f}")
    print()

    # 全样本基准
    full = {
        "P(split|holds=1)": round(m[m["holds"] == 1]["split"].mean(), 4),
        "P(split|holds=0)": round(m[m["holds"] == 0]["split"].mean(), 4),
    }
    lift_full = full["P(split|holds=1)"] / full["P(split|holds=0)"]
    full["提升比"] = round(lift_full, 2)
    print(f"全样本基准: {full}")
    print()

    # 单变量门槛扫描
    scan = scan_thresholds(m)
    print("=== 单变量门槛扫描 ===")
    print(scan.to_string(index=False))
    print()

    # 联合门槛扫描
    combo = scan_combined(m)
    print("=== 联合门槛扫描 ===")
    print(combo.to_string(index=False))
    print()

    # 特征分布：holds=1 vs holds=0
    print("=== holds 分组下的团特征 ===")
    for var in ["size", "n_mod", "e2_share", "hier_n"]:
        h1 = m[m["holds"] == 1][var]
        h0 = m[m["holds"] == 0][var]
        print(f"{var:12s}  holds=1: mean={h1.mean():.2f}  median={h1.median():.0f}  "
              f"|  holds=0: mean={h0.mean():.2f}  median={h0.median():.0f}")

    # 保存结果
    RES.mkdir(parents=True, exist_ok=True)
    scan.to_parquet(RES / "g2_threshold_scan.parquet", index=False)
    combo.to_parquet(RES / "g2_threshold_combo.parquet", index=False)

    # 写 markdown 报告
    lines = ["# g2 门槛扫描：寻找最优切分点", ""]
    lines.append(f"总样本: {len(m)}（holds=1: {len(m[m['holds']==1])}, holds=0: {len(m[m['holds']==0])}）")
    lines.append(f"split 基础率: {m['split'].mean():.4f}")
    lines.append("")
    lines.append(f"**全样本基准**：P(split|holds=1)={full['P(split|holds=1)']}, "
                 f"P(split|holds=0)={full['P(split|holds=0)']}, 提升比={full['提升比']}")
    lines.append("")
    lines.append("## 单变量门槛扫描")
    lines.append("")
    lines.append(scan.to_markdown(index=False))
    lines.append("")
    lines.append("## 联合门槛扫描")
    lines.append("")
    lines.append(combo.to_markdown(index=False))
    lines.append("")
    lines.append("## holds 分组下的团特征对比")
    lines.append("")
    lines.append("| 变量 | holds=1 (均值/中位数) | holds=0 (均值/中位数) |")
    lines.append("|------|----------------------|----------------------|")
    for var in ["size", "n_mod", "e2_share", "hier_n"]:
        h1 = m[m["holds"] == 1][var]
        h0 = m[m["holds"] == 0][var]
        lines.append(f"| {var} | {h1.mean():.2f} / {h1.median():.0f} | {h0.mean():.2f} / {h0.median():.0f} |")

    md = "\n".join(lines)
    (RES / "g2_threshold_scan.md").write_text(md, encoding="utf-8")
    print(f"\n已写出 {RES / 'g2_threshold_scan.md'}")


if __name__ == "__main__":
    main()
