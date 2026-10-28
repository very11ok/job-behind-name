"""准则三对象池 + 三条准则的后果标签（T+h, h=1,2,3）。

准则三 (c) 单元 = 企业 × 年。
  前因 = 该企业结构中存在"模板残留"：表面相似度高于结构相似度所解释的部分。
  后果 = 该企业 T+h 年新增的岗位中，属于"跨企业模板采纳"的比例上升。

后果标签（三条通用判据：新任务 → 新岗位）
  g1 (a) 岗位任务集：T+h 年该岗位（J）是否变成"混合型新组合"——
        任务集发生变化 且 新出现的任务对里出现 E 差 ≥2 的高-低搭配。
  g2 (b) 任务团：T+h 年该团是否分裂——团内任务被 ≥2 个不同的新岗位分别承载，
        且每个承载岗位的任务数小于团规模（即被拆细）。
  g3 (c) 企业：T+h 年该企业新增岗位中"跨企业模板采纳"占比 是否高于全网同年中位数。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from jtagent import pairs as P

OUT = Path(r"D:\harness office\research\jobtask-agent\out")
OBJ = OUT / "objects"
RESULTS = OUT / "results"


def _taskset(s) -> frozenset:
    return frozenset(int(x) for x in str(s).split(";") if str(x).strip())


# ── 准则一后果：岗位任务集变成"混合型新组合" ─────────────────────
def label_g1(year: int, horizons=(1, 2, 3)) -> pd.DataFrame:
    obj = pd.read_parquet(OBJ / f"g1_jobs_{year}.parquet")
    attrs = pd.read_parquet(OUT / "snapshots" / "task_dict.parquet")
    e_map = dict(zip(attrs["task"], attrs["E_ord"].fillna(1)))
    jobs_now = {r["job"]: frozenset(r["tasks"]) for _, r in obj.iterrows()}

    rows = []
    for h in horizons:
        fut = P.load_jobs(year + h) if (OUT / "snapshots" / f"jobs_{year+h}.parquet").exists() else None
        if fut is None:
            continue
        fut_by_parent = {}
        for _, r in fut.iterrows():
            fut_by_parent[r["job"]] = frozenset(int(t) for t in r["tasks"])
        for j, ts in jobs_now.items():
            f = fut_by_parent.get(j)
            if f is None:                     # 该岗位在 T+h 不存在（消失或改名）
                rows.append({"job": j, "h": h, "alive": 0, "changed": 0, "mixed_new": 0})
                continue
            new_pairs = []
            fl = sorted(f)
            for i in range(len(fl)):
                for k in range(i + 1, len(fl)):
                    a, b = fl[i], fl[k]
                    if (a, b) not in _pairset(ts):
                        new_pairs.append((a, b))
            mixed = sum(1 for a, b in new_pairs
                        if abs(e_map.get(a, 1) - e_map.get(b, 1)) >= 2)
            rows.append({
                "job": j, "h": h, "alive": 1,
                "changed": int(f != ts),
                "n_new_pairs": len(new_pairs),
                "n_mixed_new_pairs": mixed,
                "mixed_new": int(len(new_pairs) > 0 and mixed > 0),
            })
    return pd.DataFrame(rows)


def _pairset(ts: frozenset) -> set:
    tl = sorted(ts)
    return {(tl[i], tl[k]) for i in range(len(tl)) for k in range(i + 1, len(tl))}


# ── 准则二后果：任务团被拆进 ≥2 个更窄的新岗位 ──────────────────
def label_g2(year: int, horizons=(1, 2, 3)) -> pd.DataFrame:
    obj = pd.read_parquet(OBJ / f"g2_comm_{year}.parquet")
    rows = []
    for h in horizons:
        f = OUT / "snapshots" / f"jobs_{year+h}.parquet"
        if not f.exists():
            continue
        fut = P.load_jobs(year + h)
        fut_jobs = [frozenset(int(t) for t in x) for x in fut["tasks"]]
        for _, r in obj.iterrows():
            ts = _taskset(r["tasks"])
            holders = [xj for xj in fut_jobs
                       if len(xj & ts) >= 2 and len(xj) < len(ts)]
            # 分裂：至少 2 个不同岗位分别承载团的一部分，且并集覆盖团 ≥60%
            cover = len(set().union(*[xj & ts for xj in holders])) / len(ts) if holders else 0.0
            rows.append({
                "seed": r["seed"], "h": h,
                "n_holders": len(holders), "cover": round(cover, 3),
                "split": int(len(holders) >= 2 and cover >= 0.6),
            })
    return pd.DataFrame(rows)


# ── 准则三后果：企业新增岗位中跨企业模板采纳占比 ─────────────────
def label_g3(year: int, horizons=(1, 2, 3)) -> pd.DataFrame:
    from jtagent import firm_panel

    fj = firm_panel.build_firm_year_jobs()
    adopt = pd.read_parquet(RESULTS / "rule_c_adoption.parquet")
    adopt["job"] = adopt["job"].astype(str)
    tmpl = adopt.set_index("job")["xfirm_struct_sim"] if "xfirm_struct_sim" in adopt else None
    if tmpl is None:
        tmpl = adopt.set_index("job")["struct_sim"]

    firm_y = fj.groupby(["firm", "year"])["job"].apply(lambda s: set(s.astype(str)))
    rows = []
    for h in horizons:
        ys = year + h
        if not (firm_y.index.get_level_values("year") == ys).any():
            continue
        base = firm_y.xs(year, level="year")
        nxt = firm_y.xs(ys, level="year")
        pool_firms = set(pd.read_parquet(OBJ / f"g3_firms_{year}.parquet")["firm"].astype(str))
        for firm in nxt.index:
            newj = nxt[firm] - base.get(firm, set())
            if firm not in pool_firms:
                continue
            if not newj:
                rows.append({"firm": firm, "h": h, "n_new_jobs": 0,
                             "adopt_share": np.nan, "above_median": 0})
                continue
            vals = [tmpl.get(j, 0.0) for j in newj]
            rows.append({
                "firm": firm, "h": h, "n_new_jobs": len(newj),
                "adopt_share": float(np.mean([v >= 0.8 for v in vals])),
                "adopt_mean_sim": float(np.mean(vals)),
            })
    df = pd.DataFrame(rows)
    for h in sorted(df["h"].unique()):
        m = df["h"] == h
        med = df.loc[m & df["adopt_share"].notna(), "adopt_share"].median()
        df.loc[m, "median_adopt"] = med
        df.loc[m, "above_median"] = (df.loc[m, "adopt_share"] > med).astype(int)
    return df


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    y = 2020
    g1 = label_g1(y)
    g1.to_parquet(OBJ / f"labels_g1_{y}.parquet", index=False)
    print("准则一后果基础率（h=1/2/3 混合型新组合）:")
    print(g1.groupby("h")["mixed_new"].agg(["mean", "count"]).round(4).to_string())
    g2 = label_g2(y)
    g2.to_parquet(OBJ / f"labels_g2_{y}.parquet", index=False)
    print("\n准则二后果基础率（任务团分裂）:")
    print(g2.groupby("h")["split"].agg(["mean", "count"]).round(4).to_string())
    g3 = label_g3(y)
    g3.to_parquet(OBJ / f"labels_g3_{y}.parquet", index=False)
    print("\n准则三后果（逐企业：新增岗位中模板采纳占比，above_median=高于同年中位数）:")
    print(g3.groupby("h")[["n_new_jobs", "adopt_share", "above_median"]]
          .agg({"n_new_jobs": "sum", "adopt_share": "mean", "above_median": "mean"})
          .round(4).to_string())