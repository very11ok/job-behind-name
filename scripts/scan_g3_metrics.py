"""g3 修复：从 LLM 主观判定改为客观结构指标。

诊断已确认 LLM 判定无信息量（p 档排序力≈0，控制企业特征后 holds 无独立效应）。
本脚本测试每个客观结构指标作为二分前因的预测力，找有预测力的替代指标。

测试的指标：
  - surf_sim: 表层相似度（与模板的表层相似）
  - struct_sim: 结构相似度
  - xfirm_sim: 跨企业相似度
  - n_jobs: 企业岗位数
  - n_mod: 模块数
  - e2_share: 编码任务占比
  - mean_size: 平均岗位规模
  - 残差: surf_sim - struct_sim（原 LLM 判定的依据）
  - 残差2: surf_sim - xfirm_sim
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

BASE = Path(r"D:\harness office\research\jobtask-agent")
OUT = BASE / "out"
OBJ = OUT / "objects"
RES = OUT / "results"


def ttest_p(a_rate: float, a_n: int, b_rate: float, b_n: int) -> float:
    """两比例 z 检验的 p 值（正态近似）。"""
    if a_n < 5 or b_n < 5:
        return float("nan")
    p_pool = (a_rate * a_n + b_rate * b_n) / (a_n + b_n)
    if p_pool == 0 or p_pool == 1:
        return float("nan")
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / a_n + 1 / b_n))
    if se == 0:
        return float("nan")
    z = (a_rate - b_rate) / se
    return math.erfc(abs(z) / math.sqrt(2))


def cond_for_metric(m: pd.DataFrame, metric: str, label: str) -> list[dict]:
    """对单个指标做二分（中位数切分），计算各 h 下的条件概率。"""
    med = m[metric].median()
    m = m.assign(_high=m[metric] >= med, _low=m[metric] < med)
    rows = []
    for h, g in m.groupby("h"):
        hi = g[g["_high"]]
        lo = g[g["_low"]]
        p1 = hi["above_median"].mean() if len(hi) else float("nan")
        p0 = lo["above_median"].mean() if len(lo) else float("nan")
        lift = p1 / p0 if pd.notna(p1) and pd.notna(p0) and p0 > 0 else float("nan")
        p = ttest_p(p1, len(hi), p0, len(lo))
        rows.append({
            "指标": label, "h": int(h), "n": len(g),
            "n_high": len(hi), "n_low": len(lo),
            "P(adopt|高)": round(p1, 4) if pd.notna(p1) else None,
            "P(adopt|低)": round(p0, 4) if pd.notna(p0) else None,
            "提升比": round(lift, 2) if pd.notna(lift) else None,
            "p值": f"{p:.2e}" if pd.notna(p) else None,
        })
    return rows


def corr_for_metric(m: pd.DataFrame, metric: str, label: str) -> list[dict]:
    """连续变量与 adopt_share 的 Spearman 相关。"""
    rows = []
    for h, g in m.groupby("h"):
        corr = g[metric].corr(g["adopt_share"], method="spearman")
        rows.append({
            "指标": label, "h": int(h),
            "Spearman相关": round(corr, 4) if pd.notna(corr) else None,
            "n": len(g),
        })
    return rows


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    # 合并数据
    firms = pd.read_parquet(OBJ / "g3_firms_2020.parquet")
    j = pd.read_parquet(OBJ / "judge_g3_2020.parquet")
    lab = pd.read_parquet(OBJ / "labels_g3_2020.parquet")

    for df in [firms, j, lab]:
        df["firm"] = df["firm"].astype(str)

    m = j.merge(firms, on="firm", how="inner").merge(
        lab[["firm", "h", "above_median", "adopt_share"]], on="firm", how="inner"
    )

    # 计算残差
    m["residual"] = m["surf_sim"] - m["struct_sim"]
    m["residual2"] = m["surf_sim"] - m["xfirm_sim"]

    print(f"总样本: {len(m)}（holds=1: {len(m[m['holds']==1])}, holds=0: {len(m[m['holds']==0])}）")
    print(f"各 h 样本: {m.groupby('h').size().to_dict()}")
    print()

    # 1. LLM 判定基准
    print("=== LLM 判定（基准）===")
    llm_rows = cond_for_metric(m.assign(_metric=m["holds"]), "holds", "LLM判定")
    # 用 holds 做二分
    for h, g in m.groupby("h"):
        hi = g[g["holds"] == 1]
        lo = g[g["holds"] == 0]
        p1 = hi["above_median"].mean() if len(hi) else float("nan")
        p0 = lo["above_median"].mean() if len(lo) else float("nan")
        lift = p1 / p0 if pd.notna(p1) and pd.notna(p0) and p0 > 0 else float("nan")
        p = ttest_p(p1, len(hi), p0, len(lo))
        print(f"  h={h}: P(adopt|holds=1)={p1:.4f}, P(adopt|holds=0)={p0:.4f}, 提升比={lift:.2f}, p={p:.2e}")

    print()

    # 2. 客观指标扫描（二分法）
    metrics = [
        ("surf_sim", "表层相似度"),
        ("struct_sim", "结构相似度"),
        ("xfirm_sim", "跨企业相似度"),
        ("n_jobs", "岗位数"),
        ("n_mod", "模块数"),
        ("e2_share", "编码任务占比"),
        ("mean_size", "平均岗位规模"),
        ("residual", "残差(surf-struct)"),
        ("residual2", "残差(surf-xfirm)"),
    ]

    all_cond = []
    all_corr = []

    for col, label in metrics:
        rows = cond_for_metric(m, col, label)
        all_cond.extend(rows)
        corr_rows = corr_for_metric(m, col, label)
        all_corr.extend(corr_rows)
        print(f"=== {label}（{col}）===")
        for r in rows:
            print(f"  h={r['h']}: P(高)={r['P(adopt|高)']}, P(低)={r['P(adopt|低)']}, 提升比={r['提升比']}, p={r['p值']}")
        print()

    # 3. 连续相关
    print("=== 连续 Spearman 相关 ===")
    corr_df = pd.DataFrame(all_corr)
    print(corr_df.to_string(index=False))
    print()

    # 保存
    RES.mkdir(parents=True, exist_ok=True)
    cond_df = pd.DataFrame(all_cond)
    cond_df.to_parquet(RES / "g3_metric_scan.parquet", index=False)
    corr_df.to_parquet(RES / "g3_metric_corr.parquet", index=False)

    # 写 markdown
    lines = ["# g3 客观指标扫描：从 LLM 判定到结构指标", ""]
    lines.append(f"总样本: {len(m)}，各 h 下 n={m.groupby('h').size().to_dict()}")
    lines.append("")
    lines.append("## LLM 判定基准")
    lines.append("")
    lines.append("| h | P(adopt|holds=1) | P(adopt|holds=0) | 提升比 | p 值 |")
    lines.append("|---|-------------------|-------------------|--------|------|")
    for h, g in m.groupby("h"):
        hi = g[g["holds"] == 1]
        lo = g[g["holds"] == 0]
        p1 = hi["above_median"].mean() if len(hi) else float("nan")
        p0 = lo["above_median"].mean() if len(lo) else float("nan")
        lift = p1 / p0 if pd.notna(p1) and pd.notna(p0) and p0 > 0 else float("nan")
        p = ttest_p(p1, len(hi), p0, len(lo))
        lines.append(f"| {h} | {p1:.4f} | {p0:.4f} | {lift:.2f} | {p:.2e} |")
    lines.append("")
    lines.append("## 客观指标条件概率（中位数二分）")
    lines.append("")
    lines.append(cond_df.to_markdown(index=False))
    lines.append("")
    lines.append("## 连续 Spearman 相关")
    lines.append("")
    lines.append(corr_df.to_markdown(index=False))
    lines.append("")

    md = "\n".join(lines)
    (RES / "g3_metric_scan.md").write_text(md, encoding="utf-8")
    print(f"已写出 {RES / 'g3_metric_scan.md'}")


if __name__ == "__main__":
    main()
