"""原则三（模仿性模板扩散）修复验证：客观前因 n_jobs / n_mod。

LLM 判定空壳已确认，改用企业规模结构指标：
  前因 = n_jobs 高（中位数二分）、n_mod 高、两者组合
  后果 = above_median（T+h 新增岗位中跨企业模板采纳占比高于同年中位数）

输出：条件概率 + 提升比 + 反向概率 + 卡方，与 LLM holds 对照。
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

OUT = Path(r"D:\harness office\research\jobtask-agent\out")
OBJ = OUT / "objects"
RES = OUT / "results"
YEAR = 2020


def z2(a, na, b, nb):
    if na == 0 or nb == 0:
        return float("nan")
    p1, p2 = a / na, b / nb
    pp = (a + b) / (na + nb)
    se = math.sqrt(pp * (1 - pp) * (1 / na + 1 / nb))
    if se == 0:
        return float("nan")
    return math.erfc(abs((p1 - p2) / se) / math.sqrt(2))


def chi2_2x2(a, b, c, d):
    n = a + b + c + d
    if min(a + b, c + d, a + c, b + d) == 0:
        return float("nan"), float("nan")
    x2 = (a * d - b * c) ** 2 * n / ((a + b) * (c + d) * (a + c) * (b + d))
    return x2, math.erfc(math.sqrt(x2 / 2))


def main():
    firms = pd.read_parquet(OBJ / f"g3_firms_{YEAR}.parquet")
    labels = pd.read_parquet(OBJ / f"labels_g3_{YEAR}.parquet")
    judge = pd.read_parquet(OBJ / f"judge_g3_{YEAR}.parquet")
    judge["firm"] = judge["firm"].astype(str)
    holds = dict(zip(judge["firm"], judge["holds"]))

    firms["firm"] = firms["firm"].astype(str)
    med_jobs = firms["n_jobs"].median()
    med_mod = firms["n_mod"].median()
    firms["jobs_high"] = (firms["n_jobs"] > med_jobs).astype(int)
    firms["mod_high"] = (firms["n_mod"] > med_mod).astype(int)
    firms["combo"] = ((firms["jobs_high"] == 1) & (firms["mod_high"] == 1)).astype(int)
    firms["holds"] = firms["firm"].map(holds).fillna(0).astype(int)

    m = labels.merge(firms[["firm", "jobs_high", "mod_high", "combo", "holds",
                            "n_jobs", "n_mod", "e2_share", "mean_size",
                            "struct_sim", "surf_sim"]],
                     on="firm", how="inner")
    print(f"合并后样本: {len(m)}（各 h: {m.groupby('h').size().to_dict()}）")
    print(f"n_jobs 中位数={med_jobs}, n_mod 中位数={med_mod}")

    ANTE = [
        ("n_jobs高", "jobs_high"),
        ("n_mod高", "mod_high"),
        ("n_jobs高∧n_mod高", "combo"),
        ("LLM holds（对照）", "holds"),
    ]
    CONS = [("above_median", "模板采纳高于中位数"), ("adopt_share", None)]

    lines = ["# 原则三修复验证：客观规模前因 → 模板采纳后果", ""]
    lines.append(f"样本: {len(m)} 家企业×h；n_jobs 中位数={med_jobs}, n_mod 中位数={med_mod}")
    lines.append("")

    for label, col in ANTE:
        lines.append(f"## 前因 = {col}")
        for h in (1, 2, 3):
            g = m[m["h"] == h]
            a, b = g[g[col] == 1], g[g[col] == 0]
            pa, pb = a["above_median"].mean(), b["above_median"].mean()
            pv = z2(int(a["above_median"].sum()), len(a),
                    int(b["above_median"].sum()), len(b))
            ratio = pa / pb if pb > 0 else float("inf")
            # 反向概率
            rev_a = a["above_median"].sum() / max(a["above_median"].sum()
                                                  + b["above_median"].sum(), 1)
            lines.append(f"  h={h}: P(采纳高|前因=1)={pa:.4f}(n={len(a)}), "
                         f"P(采纳高|前因=0)={pb:.4f}(n={len(b)}), "
                         f"提升比={ratio:.2f}, p={pv:.3g}")
            # adopt_share 连续均值对比
            lines.append(f"        adopt_share 均值: {a['adopt_share'].mean():.4f} vs "
                         f"{b['adopt_share'].mean():.4f}")
        lines.append("")

    # 卡方
    lines.append("## 卡方（前因 × above_median）")
    for label, col in ANTE:
        row = [f"  {col}:"]
        for h in (1, 2, 3):
            g = m[m["h"] == h]
            a = int(((g[col] == 1) & (g["above_median"] == 1)).sum())
            b = int(((g[col] == 1) & (g["above_median"] == 0)).sum())
            c = int(((g[col] == 0) & (g["above_median"] == 1)).sum())
            d = int(((g[col] == 0) & (g["above_median"] == 0)).sum())
            x2, pv = chi2_2x2(a, b, c, d)
            row.append(f" h={h} chi2={x2:.2f} p={pv:.3g}")
        lines.append(" ".join(row))
    lines.append("")

    # 反向概率：P(前因|后果=1) vs P(前因|后果=0)
    lines.append("## 反向概率 P(前因=1 | 后果)")
    for label, col in ANTE:
        for h in (1, 2, 3):
            g = m[m["h"] == h]
            p1 = g[g["above_median"] == 1][col].mean()
            p0 = g[g["above_median"] == 0][col].mean()
            lines.append(f"  h={h} {col}: P(前因|采纳高)={p1:.4f} vs "
                         f"P(前因|采纳低)={p0:.4f}, 反向提升比={p1 / p0 if p0 > 0 else float('inf'):.2f}")
    lines.append("")

    # 稳健性：连续 Spearman
    lines.append("## 连续 Spearman（指标 vs adopt_share，逐 h）")
    for var in ("n_jobs", "n_mod", "e2_share", "mean_size", "struct_sim", "surf_sim"):
        for h in (1, 2, 3):
            g = m[(m["h"] == h) & m["adopt_share"].notna()]
            rho = g[var].rank().corr(g["adopt_share"].rank())
            lines.append(f"  h={h} {var}: rho={rho:.4f} (n={len(g)})")

    txt = "\n".join(lines)
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "g3_fix_verify.md").write_text(txt, encoding="utf-8")
    m.to_parquet(RES / "g3_fix_verify.parquet", index=False)
    print(txt)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
