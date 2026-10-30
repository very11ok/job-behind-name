"""复核原则二门槛版（holds ∧ hier_n>=3 → split），并与 g2_fix_verify.md 对照。"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

OUT = Path(r"D:\harness office\research\jobtask-agent\out")

obj = pd.read_parquet(OUT / "objects" / "g2_comm_2020.parquet")
judge = pd.read_parquet(OUT / "objects" / "judge_g2_2020.parquet")
judge["seed"] = judge["seed"].astype(int)
labels = pd.read_parquet(OUT / "objects" / "labels_g2_2020.parquet")

h_map = dict(zip(judge["seed"], judge["holds"]))
obj["holds"] = obj["seed"].map(h_map).fillna(0).astype(int)
obj["combo"] = ((obj["holds"] == 1) & (obj["hier_n"] >= 3)).astype(int)

m = labels.merge(obj[["seed", "holds", "hier_n", "combo"]], on="seed", how="inner")
print(f"合并样本: {len(m)}")
print(f"combo=1: {(m['combo'] == 1).sum()}")

print()
print("门槛版（holds∧hier_n>=3 → split）：")
for h in (1, 2, 3):
    g = m[m["h"] == h]
    a = int(((g["combo"] == 1) & (g["split"] == 1)).sum())
    b = int(((g["combo"] == 1) & (g["split"] == 0)).sum())
    c = int(((g["combo"] == 0) & (g["split"] == 1)).sum())
    d = int(((g["combo"] == 0) & (g["split"] == 0)).sum())
    ct = np.array([[a, b], [c, d]])
    x2, p, _, _ = stats.chi2_contingency(ct, correction=False)
    pa, pb = a / (a + b), c / (c + d)
    print(f"  h={h}: P1={pa:.4f}(n={a + b}) P0={pb:.4f}(n={c + d}) "
          f"提升={pa / pb:.2f} chi2={x2:.2f} p={p:.3g}")

print()
print("原定义（LLM holds → split）：")
for h in (1, 2, 3):
    g = m[m["h"] == h]
    a = int(((g["holds"] == 1) & (g["split"] == 1)).sum())
    b = int(((g["holds"] == 1) & (g["split"] == 0)).sum())
    c = int(((g["holds"] == 0) & (g["split"] == 1)).sum())
    d = int(((g["holds"] == 0) & (g["split"] == 0)).sum())
    ct = np.array([[a, b], [c, d]])
    x2, p, _, _ = stats.chi2_contingency(ct, correction=False)
    pa, pb = a / (a + b), c / (c + d)
    print(f"  h={h}: P1={pa:.4f}(n={a + b}) P0={pb:.4f}(n={c + d}) "
          f"提升={pa / pb:.2f} chi2={x2:.2f} p={p:.3g}")

# 补落 parquet 供后续复核
m.to_parquet(OUT / "results" / "g2_fix_verify.parquet", index=False)
print()
print("已补写 out/results/g2_fix_verify.parquet")
