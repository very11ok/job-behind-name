"""准则二（层级解绑）岗位版验证——以岗位任务集为单位（用户口径）。

前因：岗位任务集的知识不对称度 asym = std(E_ord of job tasks)，中位数二分。
后果：T+h 年该岗位任务集下面凝结出窄岗位（承载其任务子集的新岗位），
      且窄岗位任务集的不对称度低于原岗位（down_std）。
      split 仅作对照（不加方向约束）。

对象池：g1_jobs_2020（2000 岗位）。对齐键 job。
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from jtagent import pairs as P

OUT = Path(r"D:\harness office\research\jobtask-agent\out")
YEAR = 2020


def _taskset(s) -> frozenset:
    return frozenset(int(x) for x in str(s).split(";") if str(x).strip())


def z2(a, na, b, nb):
    if na == 0 or nb == 0:
        return float("nan")
    p1, p2 = a / na, b / nb
    pp = (a + b) / (na + nb)
    se = math.sqrt(pp * (1 - pp) * (1 / na + 1 / nb))
    if se == 0:
        return float("nan")
    return math.erfc(abs((p1 - p2) / se) / math.sqrt(2))


def chi2_2x2(a, b, c, d):
    n = a + b + c + d
    if min(a + b, c + d, a + c, b + d) == 0:
        return float("nan"), float("nan")
    x2 = (a * d - b * c) ** 2 * n / ((a + b) * (c + d) * (a + c) * (b + d))
    return x2, math.erfc(math.sqrt(x2 / 2))


def main():
    obj = pd.read_parquet(OUT / "objects" / "g1_jobs_2020.parquet")
    attrs = pd.read_parquet(OUT / "snapshots" / "task_dict.parquet")
    e_map = dict(zip(attrs["task"], attrs["E_ord"].fillna(1)))

    jobs = {}
    for _, r in obj.iterrows():
        ts = _taskset(r["tasks"])
        es = [e_map.get(t, 1.0) for t in ts]
        jobs[r["job"]] = {
            "ts": ts, "n": len(ts),
            "e_std": float(np.std(es)),
            "e_mean": float(np.mean(es)),
        }
    med = float(np.median([j["e_std"] for j in jobs.values()]))
    print(f"岗位对象: {len(jobs)}，岗位内任务数均值 "
          f"{np.mean([j['n'] for j in jobs.values()]):.2f}，"
          f"e_std 中位数 = {med:.4f}")

    rows = []
    for h in (1, 2, 3):
        fut = P.load_jobs(YEAR + h)
        fut_jobs = [(r["job"], frozenset(int(t) for t in r["tasks"]))
                    for _, r in fut.iterrows()]
        # 倒排索引：task -> 未来岗位索引
        inv = {}
        for i, (_, xj) in enumerate(fut_jobs):
            for t in xj:
                inv.setdefault(t, []).append(i)
        for jid, j in jobs.items():
            ts = j["ts"]
            cand = {i for t in ts for i in inv.get(t, [])}
            holders = [fut_jobs[i][1] for i in cand
                       if len(fut_jobs[i][1] & ts) >= 2 and len(fut_jobs[i][1]) < len(ts)]
            cover = (len(set().union(*[xj & ts for xj in holders])) / len(ts)
                     if holders else 0.0)
            split = int(len(holders) >= 2 and cover >= 0.6)
            h_std = [float(np.std([e_map.get(t, 1.0) for t in xj])) for xj in holders]
            h_e = [float(np.mean([e_map.get(t, 1.0) for t in xj])) for xj in holders]
            down_std = int(bool(split) and bool(h_std) and np.mean(h_std) < j["e_std"])
            down_e = int(bool(split) and bool(h_e) and np.mean(h_e) < j["e_mean"])
            rows.append({"job": jid, "h": h, "split": split,
                         "down_std": down_std, "down_e": down_e,
                         "asym_high": int(j["e_std"] > med),
                         "e_std": j["e_std"], "size": j["n"]})

    m = pd.DataFrame(rows)
    RES = OUT / "results"
    m.to_parquet(RES / "g2_job_verify.parquet", index=False)

    lines = ["# 准则二岗位版验证（层级解绑：岗位任务集不对称度 → 凝结出更低不对称的新岗位）", ""]
    lines.append(f"对象: {len(jobs)} 个岗位（T={YEAR}）；asym = 岗位任务集 E_ord 标准差，"
                 f"中位数 {med:.4f} 二分")
    lines.append("后果: split=T+h 年出现 ≥2 个承载其任务子集的窄岗位且覆盖≥60%；"
                 "down_std=split 且窄岗位不对称度低于原岗位")
    lines.append("")

    for col, name in [("down_std", "方向性后果 down_std"), ("split", "对照 split"),
                      ("down_e", "窄岗平均E更低 down_e")]:
        lines.append(f"## {name}")
        for h in (1, 2, 3):
            g = m[m["h"] == h]
            a, b = g[g["asym_high"] == 1], g[g["asym_high"] == 0]
            pa, pb = a[col].mean(), b[col].mean()
            pv = z2(int(a[col].sum()), len(a), int(b[col].sum()), len(b))
            x2, _ = chi2_2x2(int(((g["asym_high"] == 1) & (g[col] == 1)).sum()),
                             int(((g["asym_high"] == 1) & (g[col] == 0)).sum()),
                             int(((g["asym_high"] == 0) & (g[col] == 1)).sum()),
                             int(((g["asym_high"] == 0) & (g[col] == 0)).sum()))
            ratio = pa / pb if pb > 0 else float("inf")
            lines.append(f"  h={h}: P({col}|asym高)={pa:.4f}(n={len(a)}), "
                         f"P({col}|asym低)={pb:.4f}(n={len(b)}), "
                         f"提升比={ratio:.2f}, chi2={x2:.2f}, p={pv:.3g}")
        lines.append("")

    # 大岗位分层（任务多的岗位才有拆分空间）：size>=4 子样本
    lines.append("## 稳健性：size>=4 子样本（任务集够大才有拆分空间）")
    mm = m[m["size"] >= 4]
    for col in ("down_std", "split"):
        for h in (1, 2, 3):
            g = mm[mm["h"] == h]
            a, b = g[g["asym_high"] == 1], g[g["asym_high"] == 0]
            pa, pb = a[col].mean(), b[col].mean()
            pv = z2(int(a[col].sum()), len(a), int(b[col].sum()), len(b))
            lines.append(f"  {col} h={h}: {pa:.4f}(n={len(a)}) vs {pb:.4f}(n={len(b)}), "
                         f"提升比={pa / pb if pb > 0 else float('inf'):.2f}, p={pv:.3g}")
    lines.append("")

    txt = "\n".join(lines)
    (RES / "g2_job_verify.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
