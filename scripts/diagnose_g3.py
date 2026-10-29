"""g3（准则c，模仿性模板扩散）空壳诊断。

反向提升比 1.00-1.10，净对应力几乎为零。本脚本排查：
1. p档排序力检验：高p档是否对应高后果率（校准表已显示倒挂）
2. 前因收紧实验：把"占比超中位"改为更严格定义，看区分力是否恢复
3. 后果标签替换：从"存量超中位"改为"采纳增量"
4. 混淆变量检验：控制企业特征后 holds 是否有独立效应
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import numpy as np

BASE = Path(r"D:\harness office\research\jobtask-agent")
OBJ = BASE / "out" / "objects"

key, outcome = "firm", "above_median"


def ttest(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float("nan"), float("nan")
    va = a.var()
    vb = b.var()
    if va == 0 and vb == 0:
        return float("nan"), float("nan")
    se = math.sqrt(va / na + vb / nb)
    if se == 0:
        return float("nan"), float("nan")
    t = (a.mean() - b.mean()) / se
    p = math.erfc(abs(t) / math.sqrt(2))
    return float(t), float(p)


# ---------- 加载 ----------
pool = pd.read_parquet(OBJ / "g3_firms_2020.parquet")
j = pd.read_parquet(OBJ / "judge_g3_2020.parquet")
lab = pd.read_parquet(OBJ / "labels_g3_2020.parquet")

for df in (pool, j, lab):
    df["firm"] = df["firm"].astype(str)

m = (j.merge(lab, on="firm", how="inner")
       .merge(pool[["firm", "n_jobs", "mean_size", "n_mod", "e2_share", "struct_sim", "xfirm_sim", "surf_sim"]],
              on="firm", how="left"))
print(f"合并后 n={len(m)}")
print()

# ---------- 1. p档排序力检验 ----------
print("=" * 70)
print("1. p档排序力检验")
print("=" * 70)
print("如果准则c有效，高p档应对应高后果率。")
print()
for h, g in m.groupby("h"):
    print(f"--- h={h} ---")
    for pval in sorted(g["p"].unique()):
        sub = g[g["p"] == pval]
        rate = sub[outcome].mean() if len(sub) else float("nan")
        print(f"  p={pval}: n={len(sub)}, 实际后果率={rate:.4f}, holds率={sub['holds'].mean():.3f}")
    # 相关系数
    valid = g.dropna(subset=["p"])
    if len(valid) > 2:
        r = valid["p"].corr(valid[outcome], method="spearman")
        print(f"  Spearman 相关: {r:.4f}")
print()

# ---------- 2. holds × outcome 交叉表 ----------
print("=" * 70)
print("2. holds × outcome 交叉表")
print("=" * 70)
for h, g in m.groupby("h"):
    ct = pd.crosstab(g["holds"], g[outcome], margins=True)
    print(f"\nh={h} (n={len(g)}):")
    print(ct.to_string())

# ---------- 3. 前因收紧实验 ----------
print()
print("=" * 70)
print("3. 前因收紧实验")
print("=" * 70)
# 当前前因：LLM判定 holds（"模仿性模板扩散"条件）
# 实验：用 p 值作为连续度量，看 p>0.5 vs p<=0.5 的区分力
print("用 p 值分档替代 holds 二分：")
for h, g in m.groupby("h"):
    high = g[g["p"] >= 0.5]
    low = g[g["p"] < 0.5]
    if len(high) > 0 and len(low) > 0:
        r1 = high[outcome].mean()
        r0 = low[outcome].mean()
        lift = r1 / r0 if r0 > 0 else float("nan")
        print(f"  h={h}: p>=0.5 后果率={r1:.4f} (n={len(high)}), p<0.5 后果率={r0:.4f} (n={len(low)}), 提升比={lift:.2f}")

print()
print("用 p>=0.7 更严格分档：")
for h, g in m.groupby("h"):
    high = g[g["p"] >= 0.7]
    mid = g[(g["p"] >= 0.3) & (g["p"] < 0.7)]
    low = g[g["p"] < 0.3]
    for name, sub in [("高(p>=0.7)", high), ("中(0.3-0.7)", mid), ("低(p<0.3)", low)]:
        if len(sub) > 0:
            print(f"  h={h} {name}: n={len(sub)}, 后果率={sub[outcome].mean():.4f}")

# ---------- 4. 后果标签分布 ----------
print()
print("=" * 70)
print("4. 后果标签分布")
print("=" * 70)
print(f"above_median 总发生率: {m[outcome].mean():.4f}")
for h, g in m.groupby("h"):
    print(f"  h={h}: above_median率={g[outcome].mean():.4f}, n={len(g)}")

# ---------- 5. holds=1 vs holds=0 的企业特征 ----------
print()
print("=" * 70)
print("5. holds=1 vs holds=0 的企业特征对比")
print("=" * 70)
feat_vars = ["n_jobs", "mean_size", "n_mod", "e2_share", "struct_sim", "xfirm_sim", "surf_sim"]
for var in feat_vars:
    h1 = m[m["holds"] == 1][var]
    h0 = m[m["holds"] == 0][var]
    t, p = ttest(h1, h0)
    print(f"  {var}: holds=1 mean={h1.mean():.4f} (n={len(h1)}), "
          f"holds=0 mean={h0.mean():.4f} (n={len(h0)}), t={t:.3f}, p={p:.4f}")

# split=1 vs split=0 的企业特征
print()
print("--- above_median=1 vs 0 的企业特征对比 ---")
for var in feat_vars:
    sp = m[m[outcome] == 1][var]
    ns = m[m[outcome] == 0][var]
    t, p = ttest(sp, ns)
    print(f"  {var}: outcome=1 mean={sp.mean():.4f} (n={len(sp)}), "
          f"outcome=0 mean={ns.mean():.4f} (n={len(ns)}), t={t:.3f}, p={p:.4f}")

# ---------- 6. 逻辑回归 ----------
print()
print("=" * 70)
print("6. 逻辑回归（控制企业特征后 holds 的效应）")
print("=" * 70)
feat_names = ["holds"] + feat_vars
X = m[feat_names].copy()
for c in feat_names:
    X[c] = (X[c] - X[c].mean()) / X[c].std()
y = m[outcome].values
X = np.column_stack([np.ones(len(X)), X.values])

beta = np.zeros(X.shape[1])
for _ in range(200):
    eta = X @ beta
    p_pred = 1 / (1 + np.exp(-eta))
    W = np.clip(p_pred * (1 - p_pred), 1e-10, None)
    grad = X.T @ (y - p_pred)
    H = X.T @ (X * W[:, None])
    try:
        delta = np.linalg.solve(H + 1e-8 * np.eye(H.shape[0]), grad)
    except np.linalg.LinAlgError:
        delta = np.linalg.lstsq(H, grad, rcond=None)[0]
    beta = beta + delta
    if np.max(np.abs(delta)) < 1e-8:
        break

eta = X @ beta
p_pred = 1 / (1 + np.exp(-eta))
W = np.clip(p_pred * (1 - p_pred), 1e-10, None)
cov = np.linalg.inv(X.T @ (X * W[:, None]))
se = np.sqrt(np.diag(cov))

print("变量              系数       标准误     z值      p值")
print("-" * 55)
for i, name in enumerate(["const"] + feat_names):
    z = beta[i] / se[i] if se[i] > 0 else float("nan")
    pval = math.erfc(abs(z) / math.sqrt(2))
    sign = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""
    print(f"{name:16s} {beta[i]:9.4f}  {se[i]:8.4f}  {z:8.3f}  {pval:.4f} {sign}")

or_holds = math.exp(beta[1])
print(f"\nholds 的 OR = {or_holds:.4f}")
if abs(or_holds - 1) < 0.1:
    print("控制企业特征后，holds 对 above_median 几乎无独立效应，空壳确认。")
elif or_holds > 1:
    print("控制企业特征后，holds 仍有正向效应，说明此前被混淆变量掩盖。")
else:
    print("控制企业特征后，holds 出现反向效应。")
