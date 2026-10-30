"""生成 LLM 任务标注批次原料：某年活跃任务 + 暴露等级，切成批次 CSV。

输出 out/anno_input/<YEAR>/batch_000.csv ... 供子 agent 读取标注。
标注结果写 out/anno_output/<YEAR>/batch_000.json。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from jtagent import pairs as P

OUT = Path(r"D:\harness office\research\jobtask-agent\out\results")
ANNO_IN = Path(r"D:\harness office\research\jobtask-agent\out\anno_input")
ANNO_OUT = Path(r"D:\harness office\research\jobtask-agent\out\anno_output")


def prep_year(year: int, batch_size: int = 48) -> pd.DataFrame:
    edges = P.load_edges(year)
    active = pd.Series(edges["task"].unique(), name="task")
    td = pd.read_parquet(OUT.parent / "snapshots" / "task_dict.parquet")
    df = active.to_frame().merge(td[["task", "task_text", "E", "occupation"]], on="task", how="left")
    df["task_text"] = df["task_text"].fillna("").astype(str).str.strip()
    df = df[df["task_text"] != ""].reset_index(drop=True)

    # 分层排序：按暴露等级+职业 mixed，保证批内多样
    df = df.sample(frac=1, random_state=7).reset_index(drop=True)
    d_in, d_out = ANNO_IN / str(year), ANNO_OUT / str(year)
    d_in.mkdir(parents=True, exist_ok=True)
    d_out.mkdir(parents=True, exist_ok=True)
    n_batches = 0
    for k, sl in enumerate(range(0, len(df), batch_size)):
        b = df.iloc[sl:sl + batch_size][["task", "task_text"]].rename(
            columns={"task": "id", "task_text": "text"})
        b.to_csv(d_in / f"batch_{k:03d}.csv", index=False, encoding="utf-8-sig")
        n_batches += 1
    meta = {"year": year, "n_tasks": len(df), "batch_size": batch_size,
            "n_batches": n_batches, "E_dist": df["E"].value_counts().to_dict()}
    (d_in / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    print(json.dumps(meta, ensure_ascii=False))
    return df


if __name__ == "__main__":
    for y in [int(x) for x in sys.argv[1:]] or [2019]:
        prep_year(y)
