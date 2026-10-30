"""规则 (b) 的企业层面板：跨度收窄 + 拆岗事件。

单位 = 企业(关联股票代码) × 年。
跨度指标（Garicano 问题解决跨度）：
  - n_jobs           发帖的 distinct bundle 数
  - mean_size        平均岗位任务数
  - task_union       企业任务全集大小
  - mean_evar        岗位内 E_ord 方差均值
  - pair_sim         企业内 bundle 两两任务 Jaccard 均值（抽样）→ 跨度 = 1-pair_sim
  - e2_share         企业任务中 E2 占比（暴露压力）

拆岗事件：旧 bundle B（去年在 f 活跃、今年不在），且今年 f 有 ≥2 个新帖 bundle 各自与 B
重合≥2 个任务、联集覆盖 B ≥60% → 记一次拆分。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import pairs as P

OUT = Path(r"D:\harness office\research\jobtask-agent\out")
DATA = Path(r"D:\wanted\exposure\new material")


def build_firm_year_jobs(force: bool = False) -> pd.DataFrame:
    f = OUT / "results" / "firm_year_jobs.parquet"
    if f.exists() and not force:
        return pd.read_parquet(f)
    cols = ["关联股票代码", "jobmatch", "taskmatch"]
    rows = []
    for y in range(2016, 2027):
        df = pd.read_csv(DATA / "total" / "merged" / f"{y}.csv", usecols=cols,
                         dtype=str, low_memory=False)
        df.columns = ["firm", "job", "task_list"]
        df = df.dropna(subset=["firm", "job"])
        g = df.groupby(["firm", "job"]).size().rename("n_posts").reset_index()
        g["year"] = y
        rows.append(g)
    fj = pd.concat(rows, ignore_index=True)
    fj["firm"] = fj["firm"].astype(float).astype(int).astype(str).str.zfill(6)
    f.parent.mkdir(parents=True, exist_ok=True)
    fj.to_parquet(f, index=False)
    return fj


def _e_map():
    td = pd.read_parquet(OUT / "snapshots" / "task_dict.parquet")[["task", "E_ord"]]
    return dict(zip(td["task"], td["E_ord"]))


def _jobs_tasks() -> dict[str, frozenset]:
    """job id -> 任务集合（任一年个的第一个定义）。"""
    f = OUT / "results" / "_bundle_tasks.parquet"
    if f.exists():
        b = pd.read_parquet(f)
    else:
        rows = [P.load_jobs(y)[["job", "tasks"]] for y in range(2016, 2027)]
        b = pd.concat(rows).drop_duplicates("job")
        b.to_parquet(f, index=False)
    return dict(zip(b["job"], b["tasks"].map(frozenset)))


def firm_year_stats(fj: pd.DataFrame) -> pd.DataFrame:
    emap = _e_map()
    jtasks = _jobs_tasks()
    sample_pair_n = 200
    rng = np.random.default_rng(0)
    stats = []
    for (firm, y), g in fj.groupby(["firm", "year"]):
        bundles = [jtasks[j] for j in g["job"] if j in jtasks]
        if not bundles:
            continue
        sizes = np.array([len(b) for b in bundles], dtype=float)
        un = frozenset().union(*bundles)
        evars = np.array([np.var([emap.get(t, 1.0) for t in b]) if len(b) > 1 else 0.0
                          for b in bundles])
        e_all = np.array([emap.get(t, 1.0) for t in un]) if un else np.array([1.0])
        jac_vals = []
        if len(bundles) > 1:
            idx = rng.integers(0, len(bundles), size=(min(sample_pair_n, len(bundles) ** 2), 2))
            for a, b in idx:
                if a == b:
                    continue
                ta, tb = bundles[a], bundles[b]
                u = len(ta | tb)
                jac_vals.append(len(ta & tb) / u if u else 0.0)
        stats.append({
            "firm": firm, "year": int(y), "n_jobs": len(bundles),
            "n_posts": int(g["n_posts"].sum()),
            "mean_size": float(sizes.mean()), "task_union": len(un),
            "union_per_job": len(un) / len(bundles),
            "mean_evar": float(evars.mean()),
            "pair_sim": float(np.mean(jac_vals)) if jac_vals else np.nan,
            "e2_share": float((e_all == 2).mean()),
        })
    return pd.DataFrame(stats)


def detect_splits(fj: pd.DataFrame, min_overlap: int = 2, cover: float = 0.6) -> pd.DataFrame:
    jtasks = _jobs_tasks()
    events = []
    for firm, g_all in fj.groupby("firm"):
        by_year = {y: set(g["job"]) for y, g in g_all.groupby("year")}
        years = sorted(by_year)
        for y0, y1 in zip(years[:-1], years[1:]):
            gone = by_year[y0] - by_year[y1]
            new = by_year[y1] - by_year[y0]
            # 只看企业新增且任务集不算大的岗位对
            for L in gone:
                if L not in jtasks:
                    continue
                lt = jtasks[L]
                if len(lt) < 4:
                    continue
                hits = []
                for m in new:
                    if m not in jtasks:
                        continue
                    mt = jtasks[m]
                    if len(mt) >= len(lt):
                        continue
                    ov = len(mt & lt)
                    if ov >= min_overlap:
                        hits.append(m)
                if len(hits) >= 2:
                    for i in range(len(hits)):
                        for j2 in hits[i + 1:]:
                            un = jtasks[hits[i]] | jtasks[j2]
                            cov = len(un & lt) / len(lt)
                            if cov >= cover:
                                events.append({"firm": firm, "year": y1, "legacy": L,
                                               "parts": f"{hits[i]}|{j2}", "cover": cov})
                                break
                        else:
                            continue
                        break
    return pd.DataFrame(events)


def run():
    fj = build_firm_year_jobs()
    print("firm-year-job:", fj.shape)
    st = firm_year_stats(fj)
    st.to_csv(OUT / "results" / "firm_year_stats.csv", index=False, encoding="utf-8-sig")
    print(st.groupby("year")[["n_jobs", "mean_size", "union_per_job",
                              "mean_evar", "pair_sim", "e2_share"]].mean().round(4).to_string())
    ev = detect_splits(fj)
    ev.to_csv(OUT / "results" / "split_events.csv", index=False, encoding="utf-8-sig")
    print(ev.groupby("year").size().rename("拆岗事件数").to_string())
    return st, ev
