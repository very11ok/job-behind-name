"""组装年份 T 的候选任务对特征表 + T+1 形成标签。"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

from . import pairs as P

OUT = Path(r"D:\harness office\research\jobtask-agent\out")
PAIR_DIR = OUT / "pairs"
_KEY = 1_000_000  # ti*_KEY+tj 作为对键（task id < 1e5）


def _task_attrs() -> pd.DataFrame:
    from .attrs import load_attrs
    return load_attrs()


def _pair_keys(bound: set[tuple[int, int]]) -> np.ndarray:
    if not bound:
        return np.array([], dtype=np.int64)
    arr = np.fromiter((a * _KEY + b for a, b in bound), dtype=np.int64, count=len(bound))
    return np.unique(arr)


def build_pairs_table(year: int, attrs: pd.DataFrame | None = None,
                      max_candidates: int = 5_000_000, seed: int = 0) -> pd.DataFrame:
    PAIR_DIR.mkdir(parents=True, exist_ok=True)
    f = PAIR_DIR / f"pairs_{year}.parquet"
    if f.exists():
        return pd.read_parquet(f)

    eT = P.load_edges(year)
    tasks, tidx, A, deg_job, deg_pair = P.build_projection(eT)
    n = len(tasks)

    C = P.common_neighbors(A)
    if C.nnz > max_candidates:
        rng = np.random.default_rng(seed)
        keep = rng.choice(C.nnz, size=max_candidates, replace=False)
        keep.sort()
        C0 = sp.coo_matrix(C)
        C = sp.coo_matrix((C0.data[keep], (C0.row[keep], C0.col[keep])), shape=(n, n)).tocsr()
    C = sp.triu(C, k=1).tocoo()
    i, j, cn = C.row, C.col, C.data.astype(np.float32)

    df = pd.DataFrame({"ti": tasks[i].astype(np.int32), "tj": tasks[j].astype(np.int32)})
    df["cn"] = cn
    di, dj = deg_job[i], deg_job[j]
    dpi, dpj = deg_pair[i], deg_pair[j]
    df["deg_i"], df["deg_j"] = di.astype(np.int32), dj.astype(np.int32)
    df["degp_i"], df["degp_j"] = dpi.astype(np.int32), dpj.astype(np.int32)
    df["jaccard"] = cn / np.maximum(dpi + dpj - cn, 1.0)
    df["pa"] = di.astype(np.float64) * dj.astype(np.float64)

    attrs = attrs if attrs is not None else _task_attrs()
    a = attrs.set_index("task")
    for col in ("E_ord", "ctx", "codable", "module"):
        src = a[col]
        df[f"{col}_i"] = src.reindex(df["ti"]).to_numpy()
        df[f"{col}_j"] = src.reindex(df["tj"]).to_numpy()
    df["E_gap"] = (df["E_ord_i"] - df["E_ord_j"]).abs()

    pk = df["ti"].to_numpy(np.int64) * _KEY + df["tj"].to_numpy(np.int64)

    eT1 = P.load_edges(year + 1)
    boundT1 = _pair_keys(P.bound_pair_set(eT1))
    df["y"] = np.isin(pk, boundT1).astype(np.float32)

    fa = P.first_appear()
    new_jobs = set(fa.loc[fa["year"] == year + 1, "job"])
    bound_new = _pair_keys(P.bound_pair_set(eT1[eT1["job"].isin(new_jobs)]))
    df["y_new"] = np.isin(pk, bound_new).astype(np.float32)

    try:
        eT0 = P.load_edges(year - 1)
        boundT0 = _pair_keys(P.bound_pair_set(eT0))
        df["bind_TM1"] = np.isin(pk, boundT0).astype(np.float32)
    except FileNotFoundError:
        df["bind_TM1"] = 0.0

    df["year"] = year
    df.to_parquet(f, index=False)
    return df


def summarize(df: pd.DataFrame) -> dict:
    return {
        "candidates": len(df),
        "positives": int(df["y"].sum()),
        "pos_rate": round(float(df["y"].mean()), 6),
        "positives_new_bundle": int(df["y_new"].sum()),
    }
