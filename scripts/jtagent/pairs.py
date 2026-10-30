"""候选任务对生成、网络结构特征、形成/消亡标签。

对年份 T：
  - 投影 A(T)：任务×任务 0/1（同岗共现）
  - 候选集 = 2-hop 且未捆绑：cn>0, A=0
  - 标签 y=1[该对在 T+1 捆绑]；y_new=1[T+1 捆绑它的岗位是 T+1 新岗位]
  - 图特征：deg, cn, jaccard, adamic-adar
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

SNAP = Path(r"D:\harness office\research\jobtask-agent\out\snapshots")


def load_edges(year: int) -> pd.DataFrame:
    return pd.read_parquet(SNAP / f"edges_{year}.parquet")


def load_jobs(year: int) -> pd.DataFrame:
    return pd.read_parquet(SNAP / f"jobs_{year}.parquet")


def bound_pair_set(edges: pd.DataFrame) -> set[tuple[int, int]]:
    out = set()
    grp = edges.groupby("job")["task"]
    for _, part in grp:
        arr = np.sort(part.unique())
        for i in range(len(arr)):
            a = int(arr[i])
            for b in arr[i + 1:]:
                out.add((a, int(b)) if a < int(b) else (int(b), a))
    return out


def build_projection(edges: pd.DataFrame):
    """返回 (tasks 排好序的 id 数组, tidx, A 邻接 csr int, deg 每任务的岗位度)。"""
    tasks = np.sort(edges["task"].unique())
    tidx = {int(t): i for i, t in enumerate(tasks)}
    jobs, jidx_map = pd.factorize(edges["job"])
    r, c = jobs, edges["task"].map(tidx).to_numpy()
    B = sp.csr_matrix((np.ones(len(edges), np.float32), (r, c)),
                      shape=(len(jidx_map), len(tasks)))
    W = B.T @ B
    W.setdiag(0)
    W.eliminate_zeros()
    A = (W > 0).astype(np.int32).tocsr()
    deg_job = np.asarray((B > 0).astype(np.int32).sum(axis=0)).ravel()  # 岗位度
    deg_pair = np.asarray(A.sum(axis=1)).ravel()                        # 共现邻域度
    return tasks, tidx, A, deg_job, deg_pair


def common_neighbors(A: sp.spmatrix) -> sp.spmatrix:
    """未捆绑且 cn>0 的上三角候选矩阵；数值 = 共邻数。int32 防溢出。"""
    C = A @ A.T
    C = C.multiply(A == 0)
    C.setdiag(0)
    C.eliminate_zeros()
    return sp.triu(C, k=1).tocsr()


def adamic_adar(A: sp.spmatrix, deg_pair: np.ndarray) -> sp.spmatrix:
    w = 1.0 / np.log(np.maximum(deg_pair, 2.0))
    M = A @ sp.diags(w.astype(np.float32))
    AA = M @ A.T
    AA = AA.multiply(A == 0)
    AA.setdiag(0)
    AA.eliminate_zeros()
    return sp.triu(AA, k=1).tocsr()


def first_appear() -> pd.DataFrame:
    f = pd.read_csv(r"D:\wanted\exposure\new material\total\newjob\first_appear.csv")
    f = f.rename(columns={"num": "job", "date": "year"}).dropna(subset=["job"])
    f["year"] = f["year"].astype(int)
    return f
