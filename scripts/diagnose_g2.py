"""g2（准则b，层级解绑）反向关系诊断。

反向提升比 0.51-0.57，方向相反。本脚本排查：
1. 混淆变量分层：按团规模、模板数、同层占比、层级数分组，看反向关系是否一致
2. 机制中间环节：检查 holds=1 的团是否有"上层吸收"的中间证据
3. 标签合理性：检查 split 标签的分布与特征
"""
from __future__ import annotations

import sys
import math
from pathlib import Path

import pandas as pd
import numpy as np

BASE = Path(r"D:\harness office\research\jobtask-agent")
OBJ = BASE / "out" / "objects"
RES = BASE / "out" / "results"

key, outcome = "seed", "split"


def ttest(a, b):
    """简单 t 检验（正态近似 p 值），不依赖 scipy。"""
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
pool = pd.read_parquet(OBJ / "g2_comm_2020.parquet")
j = pd.read_parquet(OBJ / "judge_g2_2020.parquet")
lab = pd.read_parquet(OBJ / "labels_g2_2020.parquet")

for df in (pool, j, lab):
    df["seed"] = df["seed"].astype(str)

m = (j.merge(lab, on="seed", how="inner")
       .merge(pool[["seed", "size", "n_mod", "e2_share", "hier_n"]], on="seed", how="left"))
print(f"合并后 n={len(m)}")
print()

# ---------- 1. 混淆变量分层 ----------
print("=" * 70)
print("1. 混淆变量分层分析")
print("=" * 70)

confound_vars = ["size", "n_mod", "e2_share", "hier_n"]

for var in confound_vars:
    print(f"\n--- 按 {var} 分层 ---")
    qcut = pd.qcut(m[var], 3, labels=["低", "中", "高"])
    for label, g in m.groupby(qcut):
        a = g[g["holds"] == 1]
        b = g[g["holds"] == 0]
        p1 = a[outcome].mean() if len(a) else float("nan")
        p0 = b[outcome].mean() if len(b) else float("nan")
        lift = round(p1 / p0, 2) if pd.notna(p1) and pd.notna(p0) and p0 > 0 else float("nan")
        print(f"  {label}: n={len(g)}, holds率={g['holds'].mean():.3f}, "
              f"P(outcome|holds=1)={p1:.4f}, P(outcome|holds=0)={p0:.4f}, 提升比={lift}")

# ---------- 2. 机制中间环节 ----------
print()
print("=" * 70)
print("2. 机制中间环节检验")
print("=" * 70)
print("准则b链条：凝聚团(holds=1) → 上层吸收 → 下层分裂")

print("\n--- holds=1 vs holds=0 的团特征对比 ---")
for var in ["size", "n_mod", "e2_share", "hier_n"]:
    h1 = m[m["holds"] == 1][var]
    h0 = m[m["holds"] == 0][var]
    t, p = ttest(h1, h0)
    print(f"  {var}: holds=1 mean={h1.mean():.4f} (n={len(h1)}), "
          f"holds=0 mean={h0.mean():.4f} (n={len(h0)}), t={t:.3f}, p={p:.4f}")

# ---------- 3. 标签合理性 ----------
print()
print("=" * 70)
print("3. split 标签分布与特征")
print("=" * 70)
print(f"split 总发生率: {m[outcome].mean():.4f}")
print("按 h 分组:")
for h, g in m.groupby("h"):
    print(f"  h={h}: split率={g[outcome].mean():.4f}, n={len(g)}")

print("\n--- split=1 vs split=0 的团特征对比 ---")
for var in ["size", "n_mod", "e2_share", "hier_n"]:
    sp = m[m[outcome] == 1][var]
    ns = m[m[outcome] == 0][var]
    t, p = ttest(sp, ns)
    print(f"  {var}: split=1 mean={sp.mean():.4f} (n={len(sp)}), "
          f"split=0 mean={ns.mean():.4f} (n={len(ns)}), t={t:.3f}, p={p:.4f}")

# ---------- 4. holds × outcome 交叉表 ----------
print()
print("=" * 70)
print("4. holds × outcome 交叉表（按 h）")
print("=" * 70)
for h, g in m.groupby("h"):
    ct = pd.crosstab(g["holds"], g[outcome], margins=True)
    print(f"\nh={h}:")
    print(ct.to_string())

# ---------- 5. 回归：控制混淆变量后 holds 的效应 ----------
print()
print("=" * 70)
print("5. 逻辑回归（控制混淆变量后 holds 的效应）")
print("=" * 70)
# 用简单的 Wald 检验，不依赖 statsmodels
# y = split, X = [holds, size, n_mod, e2_share, hier_n]
# 标准化变量
feat_names = ["holds", "size", "n_mod", "e2_share", "hier_n"]
X = m[feat_names].copy()
for c in feat_names:
    X[c] = (X[c] - X[c].mean()) / X[c].std()
y = m[outcome].values

# 加常数
X = np.column_stack([np.ones(len(X)), X.values])

try:
    # 逻辑回归（Newton-Raphson，手工实现）
    beta = np.zeros(X.shape[1])
    for _ in range(100):
        eta = X @ beta
        p = 1 / (1 + np.exp(-eta))
        W = p * (1 - p)
        # 避免除零
        W = np.clip(W, 1e-10, None)
        grad = X.T @ (y - p)
        H = X.T @ (X * W[:, None])
        try:
            delta = np.linalg.solve(H + 1e-8 * np.eye(H.shape[0]), grad)
        except np.linalg.LinAlgError:
            delta = np.linalg.lstsq(H, grad, rcond=None)[0]
        beta = beta + delta
        if np.max(np.abs(delta)) < 1e-8:
            break

    # 协方差矩阵
    eta = X @ beta
    p = 1 / (1 + np.exp(-eta))
    W = np.clip(p * (1 - p), 1e-10, None)
    cov = np.linalg.inv(X.T @ (X * W[:, None]))
    se = np.sqrt(np.diag(cov))

    print("变量           系数       标准误     z值      p值")
    print("-" * 50)
    for i, name in enumerate(["const"] + feat_names):
        z = beta[i] / se[i] if se[i] > 0 else float("nan")
        pval = math.erfc(abs(z) / math.sqrt(2))
        sign = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""
        print(f"{name:14s}  {beta[i]:8.4f}  {se[i]:8.4f}  {z:8.3f}  {pval:.4f} {sign}")
    print(f"\nholds 的系数为 {beta[1]:.4f}，意味着 holds=1 相比 holds=0，")
    print(f"odds ratio = {math.exp(beta[1]):.4f}")
    if math.exp(beta[1]) < 1:
        print("即控制混淆变量后，holds=1 的 split odds 仍然低于 holds=0，反向关系仍在。")
    else:
        print("即控制混淆变量后，holds=1 的 split odds 高于 holds=0，反向关系消失。")
except Exception as e:
    print(f"回归失败: {e}")
