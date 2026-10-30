"""合并 LLM 任务标注批次 -> out/results/anno_<YEAR>.parquet，并做校验与回填策略输出。

用法：python merge_anno.py 2019
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

BASE = Path(r"D:\harness office\research\jobtask-agent\out")
REQ = ["id", "codability", "judgment", "coordination", "accountability",
       "embodied", "hierarchy", "module"]
MODS = {"生产执行", "质量检验", "研发技术", "工艺工程", "设备维护", "销售", "市场",
        "采购供应链", "物流仓储", "人力资源", "财务会计", "行政法务", "IT数据",
        "EHS安全", "客户服务", "综合管理", "其他"}


def merge_year(year: int):
    d_in, d_out = BASE / "anno_input" / str(year), BASE / "anno_output" / str(year)
    meta = json.loads((d_in / "meta.json").read_text("utf-8"))
    rows, bad = [], []
    for k in range(meta["n_batches"]):
        f = d_out / f"batch_{k:03d}.json"
        if not f.exists():
            bad.append(f.stem)
            continue
        try:
            arr = json.loads(f.read_text(encoding="utf-8-sig"))
            for x in arr:
                if all(key in x for key in REQ):
                    rows.append(x)
        except Exception:
            bad.append(f.stem)
    df = pd.DataFrame(rows).drop_duplicates("id")
    df["module"] = df["module"].where(df["module"].isin(MODS), "其他")
    df.to_parquet(BASE / "results" / f"anno_{year}.parquet", index=False)

    # 覆盖率
    covered = df["id"].nunique()
    print(f"[{year}] 标注 {len(df)} 条，涵盖 {covered}/{meta['n_tasks']} 任务；坏批 {len(bad)}: {bad[:10]}")

    # 与 GPT-4 暴露等级的一致性（校准证据）
    td = pd.read_parquet(BASE / "snapshots" / "task_dict.parquet")
    m = df.merge(td[["task", "E_ord", "E"]], left_on="id", right_on="task")
    if len(m):
        ct = pd.crosstab(m["E_ord"], m["codability"], normalize="index").round(3)
        print("codability × GPT-4 E_ord 行归一交叉表：")
        print(ct.to_string())
    return bad


if __name__ == "__main__":
    for y in [int(x) for x in sys.argv[1:]] or [2019]:
        merge_year(y)
