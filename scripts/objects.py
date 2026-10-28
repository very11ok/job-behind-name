"""三条准则的对象池构建：定义单元、候选对象、采样。

准则一 (a) 单元 = 岗位任务集；前因 = 高暴露可编码任务 × 语境嵌入任务共存。
准则二 (b) 单元 = 任务团（投影层连通簇）；前因 = 同层级可编码、邻域凝聚。
准则三 (c) 单元 = 企业×年；前因 = 跨企业模板残留。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

sys.path.insert(0, str(Path(__file__).parent))
from jtagent import pairs as P
from jtagent.attrs import load_attrs

OUT = Path(r"D:\harness office\research\jobtask-agent\out")
OBJ = OUT / "objects"


def _attrs():
    return load_attrs(mode="llm")


def g1_jobs(attrs: pd.DataFrame, year: int, n_sample: int = 2000, seed=0) -> pd.DataFrame:
    """准则一对象池：该年所有岗位任务集（≥2 任务），带前因初判所需字段。"""
    jobs = P.load_jobs(year)
    a = attrs.set_index("task")
    recs = []
    for _, r in jobs.iterrows():
        ts = [t for t in r["tasks"] if t in a.index]
        if len(ts) < 2:
            continue
        sub = a.loc[ts]
        recs.append({
            "job": r["job"], "year": year, "size": len(ts),
            "tasks": ";".join(str(int(t)) for t in ts),
            "e_ord": ",".join(f"{v:.0f}" for v in sub["E_ord"].fillna(1)),
            "cod": ",".join(f"{v:.2f}" if pd.notna(v) else "na" for v in sub["codable"]),
            "ctx": ",".join(f"{v:.2f}" if pd.notna(v) else "na" for v in sub["ctx"]),
            "mod": "|".join(str(m) for m in sub["module"]),
            "has_E2": int((sub["E_ord"] >= 2).any()),
            "has_E0": int((sub["E_ord"] <= 0).any()),
            "n_mod": sub["module"].nunique(),
        })
    df = pd.DataFrame(recs)
    if n_sample and len(df) > n_sample:
        df = df.sample(n_sample, random_state=seed).reset_index(drop=True)
    return df


def g2_communities(year: int, n_sample: int = 2000, seed=0) -> pd.DataFrame:
    """准则二对象池：任务团 = 投影层中一个任务及其强邻域组成的紧密任务簇。

    以每个任务为种子，取其在加权投影中权重最高、且同属一个社区的核心任务作邻居，
    组成 3–15 个任务的团。这样得到足够多的可检验对象，且"团"确实是投影层上连在一起的任务集。
    """
    cdir = Path(r"D:\wanted\exposure\new material\community") / str(year)
    core = pd.read_csv(cdir / f"core_tasks_{year}.csv")
    core = core[core["is_core"] == True]
    comm_of = dict(zip(core["task_id"].astype(int), core["comm"].astype(int)))

    edges = P.load_edges(year)
    tasks, tidx, A, deg_job, deg_pair = P.build_projection(edges)
    W = A.tocsr()  # 0/1 共现，取强邻域用度排序即可
    attrs = _attrs().set_index("task")
    pos = {int(t): i for i, t in enumerate(tasks)}

    recs = []
    for t in tasks:
        ti = int(t)
        if ti in pos and ti in comm_of:
            i = pos[ti]
            nbrs = W.indices[W.indptr[i]:W.indptr[i + 1]]
            # 只保留同社区邻居，按岗位度降序取前 8 个
            same = [int(tasks[j]) for j in nbrs if comm_of.get(int(tasks[j])) == comm_of[ti]]
            if len(same) < 2:
                continue
            same.sort(key=lambda x: -deg_job[pos[x]] if x in pos else 0)
            grp = [ti] + same[:8]
            if not (3 <= len(grp) <= 15):
                continue
            sub = attrs.reindex(grp)
            recs.append({
                "year": year, "seed": ti, "comm": comm_of[ti], "size": len(grp),
                "tasks": ";".join(str(x) for x in grp),
                "e_ord": ",".join(f"{v:.0f}" for v in sub["E_ord"].fillna(1)),
                "cod": ",".join(f"{v:.2f}" if pd.notna(v) else "na" for v in sub["codable"]),
                "hier": "|".join(str(h) for h in sub["hierarchy"].fillna("na")),
                "mod": "|".join(str(m) for m in sub["module"]),
                "n_mod": int(sub["module"].nunique()),
                "e2_share": float((sub["E_ord"] >= 2).mean()),
                "hier_n": int(sub["hierarchy"].nunique()),
            })
    df = pd.DataFrame(recs).drop_duplicates(subset=["tasks"])
    print(f"    任务团候选 {len(df)} 个", end="")
    if n_sample and len(df) > n_sample:
        df = df.sample(n_sample, random_state=seed).reset_index(drop=True)
    print(f" → 抽样 {len(df)} 个（平均 {df['size'].mean():.1f} 任务）")
    return df


def g3_firms(year: int, n_sample: int = 2000, seed=0) -> pd.DataFrame:
    """准则三对象池：企业 × 年。前因字段 = 该企业岗位结构的模板烙印特征。"""
    from jtagent import firm_panel

    fj = firm_panel.build_firm_year_jobs()
    adopt = pd.read_parquet(OUT / "results" / "rule_c_adoption.parquet")
    adopt["job"] = adopt["job"].astype(str)
    smap = adopt.set_index("job")

    sub = fj[fj["year"] == year]
    jobs = P.load_jobs(year)
    jobs["job"] = jobs["job"].astype(str)
    tset = dict(zip(jobs["job"], jobs["tasks"]))
    attrs = _attrs().set_index("task")

    recs = []
    for firm, g in sub.groupby("firm"):
        js = [j for j in g["job"].astype(str) if j in tset]
        if len(js) < 2:
            continue
        allt = set().union(*[set(tset[j]) for j in js])
        if not allt:
            continue
        a_sub = attrs.reindex(list(allt))
        struct = [smap["struct_sim"].get(j, np.nan) for j in js]
        xfirm = [smap["xfirm_struct_sim"].get(j, np.nan) for j in js]
        surf = [smap["surf_sim"].get(j, np.nan) for j in js]
        recs.append({
            "firm": firm, "year": year, "n_jobs": len(js),
            "mean_size": float(np.mean([len(tset[j]) for j in js])),
            "n_mod": int(a_sub["module"].nunique()),
            "e2_share": float((a_sub["E_ord"] >= 2).mean()),
            "struct_sim": float(np.nanmean(struct)) if np.isfinite(struct).any() else 0.0,
            "xfirm_sim": float(np.nanmean(xfirm)) if np.isfinite(xfirm).any() else 0.0,
            "surf_sim": float(np.nanmean(surf)) if np.isfinite(surf).any() else 0.0,
        })
    df = pd.DataFrame(recs)
    if n_sample and len(df) > n_sample:
        df = df.sample(n_sample, random_state=seed).reset_index(drop=True)
    print(f"    企业对象 {len(df)} 家（模板跨企相似均值 {df['xfirm_sim'].mean():.3f}）")
    return df


def build(year: int, n_sample: int = 2000):
    OBJ.mkdir(parents=True, exist_ok=True)
    a = _attrs()
    j = g1_jobs(a, year, n_sample)
    j.to_parquet(OBJ / f"g1_jobs_{year}.parquet", index=False)
    c = g2_communities(year, n_sample)
    c.to_parquet(OBJ / f"g2_comm_{year}.parquet", index=False)
    f3 = g3_firms(year, n_sample)
    f3.to_parquet(OBJ / f"g3_firms_{year}.parquet", index=False)
    print(f"[{year}] 准则一对象 {len(j)}（含E2且含E0: {int((j.has_E2.eq(1)&j.has_E0.eq(1)).sum())}）; "
          f"准则二任务团 {len(c)}（平均 {c['size'].mean():.1f} 任务）; 准则三企业 {len(f3)}")
    return j, c, f3


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for y in [int(x) for x in sys.argv[1:]] or [2020]:
        build(y)
