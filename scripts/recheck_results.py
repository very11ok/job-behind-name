"""独立复核：用 scipy.stats 重算三准则修复的关键检验，与手写公式对照。"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

OUT = Path(r"D:\harness office\research\jobtask-agent\out")
RES = OUT / "results"

print("=== 1) 原则三 g3_fix_verify 复核 ===")
m = pd.read_parquet(RES / "g3_fix_verify.parquet")
for col in ("jobs_high", "mod_high", "combo", "holds"):
    for h in (1, 2, 3):
        g = m[m["h"] == h]
        a = int(((g[col] == 1) & (g["above_median"] == 1)).sum())
        b = int(((g[col] == 1) & (g["above_median"] == 0)).sum())
        c = int(((g[col] == 0) & (g["above_median"] == 1)).sum())
        d = int(((g[col] == 0) & (g["above_median"] == 0)).sum())
        ct = np.array([[a, b], [c, d]])
        x2, p, _, _ = stats.chi2_contingency(ct, correction=False)
        pa, pb = a / (a + b), c / (c + d)
        print(f"  {col} h={h}: P1={pa:.4f} P0={pb:.4f} 提升={pa / pb:.2f} "
              f"chi2={x2:.2f} p={p:.3g}")

print()
print("=== 2) 原则二 g2_direction_verify 复核 ===")
d2 = pd.read_parquet(RES / "g2_direction_verify.parquet")
for h in (1, 2, 3):
    g = d2[d2["h"] == h]
    a = int(((g["asym_high"] == 1) & (g["down_std"] == 1)).sum())
    b = int(((g["asym_high"] == 1) & (g["down_std"] == 0)).sum())
    c = int(((g["asym_high"] == 0) & (g["down_std"] == 1)).sum())
    dd = int(((g["asym_high"] == 0) & (g["down_std"] == 0)).sum())
    ct = np.array([[a, b], [c, dd]])
    x2, p, _, _ = stats.chi2_contingency(ct, correction=False)
    pa, pb = a / (a + b), c / (c + dd)
    print(f"  asym→down_std h={h}: P1={pa:.4f} P0={pb:.4f} 提升={pa / pb:.2f} "
          f"chi2={x2:.2f} p={p:.3g}")

print()
print("=== 3) 原则二门槛版 g2_fix_verify 复核 ===")
d3 = pd.read_parquet(RES / "g2_fix_verify.parquet")
print("  列:", list(d3.columns))

print()
print("=== 4) 样本一致性检查 ===")
obj2 = pd.read_parquet(OUT / "objects" / "g2_comm_2020.parquet")
lab2 = pd.read_parquet(OUT / "objects" / "labels_g2_2020.parquet")
print(f"  g2 种子团: {obj2['seed'].nunique()} 团 / 标签行 {len(lab2)} "
      f"(= {obj2['seed'].nunique()} × 3 = {obj2['seed'].nunique() * 3})")
obj3 = pd.read_parquet(OUT / "objects" / "g3_firms_2020.parquet")
lab3 = pd.read_parquet(OUT / "objects" / "labels_g3_2020.parquet")
print(f"  g3 企业: {obj3['firm'].nunique()} 家 / 标签行 {len(lab3)}（无新岗企业各 h 缺行）")
judge2 = pd.read_parquet(OUT / "objects" / "judge_g2_2020.parquet")
judge3 = pd.read_parquet(OUT / "objects" / "judge_g3_2020.parquet")
print(f"  judge g2: {len(judge2)} 行（seed 覆盖 {judge2['seed'].astype(int).nunique()}）"
      f" / judge g3: {len(judge3)} 行")

print()
print("=== 5) 缺失与 NaN 检查 ===")
print(f"  g3_fix m 中 above_median NaN: {m['above_median'].isna().sum()}")
print(f"  g3 adopt_share NaN 行: {m['adopt_share'].isna().sum()}（n_new_jobs=0 的企业）")
print(f"  holds 缺失被填 0 的行: {(m['holds'] == 0).sum()}")
