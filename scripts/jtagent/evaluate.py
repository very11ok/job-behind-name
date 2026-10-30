"""评估指标：AP、ROC-AUC、precision@k、lift@pct、以及训练-预测式 logistic 的 Brier。"""
from __future__ import annotations

import numpy as np
import pandas as pd


def rank_metrics(y: np.ndarray, score: np.ndarray, name: str = "") -> dict:
    y = np.asarray(y, dtype=np.float64)
    score = np.asarray(score, dtype=np.float64)
    n = len(y)
    npos = max(int(y.sum()), 1)
    order = np.argsort(-score, kind="mergesort")
    ys = y[order]
    k = npos
    prec_k = float(ys[:k].mean())
    base_rate = float(y.mean())
    # Average Precision
    tp = ys.cumsum()
    ap = float((ys * tp / np.arange(1, n + 1)).sum() / npos)
    # ROC AUC (rank-based)：ranks 按分数升序，P(score_pos > score_neg)
    ranks = np.empty(n)
    ranks[order] = np.arange(n, 0, -1)   # 高分得大 rank
    nneg = n - npos
    auc = float((ranks[y == 1].sum() - npos * (npos + 1) / 2) / max(npos * nneg, 1))
    # lift at 1%
    m = max(n // 100, 1)
    lift1 = float(ys[:m].mean() / max(base_rate, 1e-12))
    return {"score": name, "AP": round(ap, 5), "AUC": round(auc, 4),
            f"P@{k}": round(prec_k, 5), "lift@1%": round(lift1, 2),
            "random_ref": round(base_rate, 6)}


def eval_frame(df: pd.DataFrame, score_names: list[str], target: str = "y") -> pd.DataFrame:
    rows = []
    y = df[target].to_numpy()
    for s in score_names:
        rows.append(rank_metrics(y, df[s].to_numpy(), name=s))
    return pd.DataFrame(rows)
