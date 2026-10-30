"""构建年度岗位—任务网络快照，并缓存为 parquet。

输入（用户既有数据）：
  <DATA>/total/merged/YYYY.csv      招聘公告级长表：jobmatch(J id), taskmatch(";"分隔任务id), exposure(岗位级)
  <DATA>/community/dict/onet_tasks.csv   O*NET 任务原文 task_id, task_text, occupation_title
  <DATA>/idmapping.csv              任务级 GPT-4 暴露等级 元素=task_id, gpt4_exposure=E0/E1/E2

输出：
  <OUT>/snapshots/jobs_YYYY.parquet   job, tasks(list), name, firm, industry, exposure, n_postings
  <OUT>/snapshots/edges_YYYY.parquet  job, task
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DATA = Path(r"D:\wanted\exposure\new material")
OUT = Path(r"D:\harness office\research\jobtask-agent\out")

YEARS = list(range(2016, 2027))

COLS = {
    "jobmatch": "job",
    "taskmatch": "task_list",
    "exposure": "exposure",
    "招聘岗位": "name",
    "企业名称": "firm",
    "股票简称": "ticker_name",
    "上市公司行业": "industry",
}


def _parse_tasks(s: str) -> list[int]:
    out = []
    for piece in str(s).split(";"):
        piece = piece.strip()
        if not piece:
            continue
        try:
            out.append(int(float(piece)))
        except ValueError:
            continue
    # 去重但保序
    seen, uniq = set(), []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def build_year(year: int, data: Path, out: Path) -> dict:
    f = data / "total" / "merged" / f"{year}.csv"
    df = pd.read_csv(f, usecols=list(COLS), dtype=str, encoding="utf-8", low_memory=False)
    df = df.rename(columns=COLS)
    for c in ("name", "firm", "ticker_name", "industry"):
        df[c] = df[c].fillna("").astype(str).str.strip()
    df["exposure"] = pd.to_numeric(df["exposure"], errors="coerce")

    # 岗位级折叠：同一 J 的任务集合按构造固定，取首现的岗位名/企业
    df["n"] = 1
    g = df.groupby("job", sort=False).agg(
        task_list=("task_list", "first"),
        name=("name", "first"),
        firm=("firm", "first"),
        ticker_name=("ticker_name", "first"),
        industry=("industry", "first"),
        exposure=("exposure", "first"),
        n_postings=("n", "sum"),
    ).reset_index()

    g["tasks"] = g["task_list"].map(_parse_tasks)
    g = g[g["tasks"].map(len) > 0].copy()

    # 一致性检查：同一 J 的任务列表是否唯一
    uniq_check = df.groupby("job")["task_list"].nunique()
    n_inconsistent = int((uniq_check > 1).sum())

    jobs = g[["job", "tasks", "name", "firm", "ticker_name", "industry", "exposure", "n_postings"]]
    edges = jobs[["job", "tasks"]].explode("tasks").rename(columns={"tasks": "task"})
    edges["task"] = edges["task"].astype(int)

    snap = out / "snapshots"
    snap.mkdir(parents=True, exist_ok=True)
    jobs.to_parquet(snap / f"jobs_{year}.parquet", index=False)
    edges.to_parquet(snap / f"edges_{year}.parquet", index=False)

    return {
        "year": year,
        "n_postings": int(df["n"].sum()),
        "n_jobs": len(jobs),
        "n_tasks": int(edges["task"].nunique()),
        "n_pairs": len(edges),
        "n_inconsistent_jobs": n_inconsistent,
    }


def build_task_dict(data: Path, out: Path) -> pd.DataFrame:
    """任务属性表：原文 + 暴露等级 + 职业广度。"""
    tx = pd.read_csv(data / "community" / "dict" / "onet_tasks.csv", encoding="utf-8")
    tx = tx.rename(columns={"task_id": "task", "task_text": "task_text",
                            "occupation_title": "occupation", "onet_soc": "soc"})
    tx["task"] = tx["task"].astype(int)

    idm = pd.read_csv(data / "idmapping.csv", encoding="utf-8")
    idm = idm.rename(columns={"元素": "task", "Title": "occ_title",
                              "gpt4_exposure": "E", "gpt4_automation": "auto",
                              "human_exposure_agg": "E_human", "human_labels": "E_label"})
    idm["task"] = pd.to_numeric(idm["task"], errors="coerce")
    idm = idm.dropna(subset=["task"])
    idm["task"] = idm["task"].astype(int)
    idm = idm[["task", "E", "E_human", "auto"]].drop_duplicates("task")

    td = tx.merge(idm, on="task", how="left")
    td["E"] = td["E"].fillna("E1")
    td["E_ord"] = td["E"].map({"E0": 0, "E1": 1, "E2": 2}).astype(float)
    snap = out / "snapshots"
    snap.mkdir(parents=True, exist_ok=True)
    td.to_parquet(snap / "task_dict.parquet", index=False)
    return td


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DATA))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    data, out = Path(args.data), Path(args.out)

    rows = []
    for y in YEARS:
        if not (data / "total" / "merged" / f"{y}.csv").exists():
            print(f"[skip] {y}")
            continue
        r = build_year(y, data, out)
        rows.append(r)
        print(f"[ok] {y}: postings={r['n_postings']:,} jobs={r['n_jobs']:,} "
              f"tasks={r['n_tasks']:,} pairs={r['n_pairs']:,} inconsistent={r['n_inconsistent_jobs']}")
        if r["n_inconsistent_jobs"]:
            print(f"     !! {r['n_inconsistent_jobs']} 个 J 在不同公告里任务集合不一致")

    summ = pd.DataFrame(rows)
    td = build_task_dict(data, out)
    print(f"[ok] task_dict: {len(td)} tasks, E dist={td['E'].value_counts().to_dict()}")
    missing = int(td["E_human"].isna().sum())
    print(f"     E 缺失 {missing} 条（已回填 E1）")
    (out / "results").mkdir(parents=True, exist_ok=True)
    summ.to_csv(out / "results" / "snapshot_summary.csv", index=False, encoding="utf-8-sig")
    print(summ.to_string(index=False))


if __name__ == "__main__":
    main()