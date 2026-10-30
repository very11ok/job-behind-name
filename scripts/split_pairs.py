"""把 >40MB 的 pairs 文件按行对半拆成 _part1/_part2（Contents API 40MB 线下）。"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

SRC = Path(r"D:\harness office\research\jobtask-agent\out\pairs")
DST = Path(r"D:\harness office\research\jobtask-agent\out\pairs_split")

BIG = ["pairs_2018.parquet", "pairs_2021.parquet", "pairs_2022.parquet",
       "pairs_2024.parquet", "pairs_2025.parquet"]

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    DST.mkdir(exist_ok=True)
    for name in BIG:
        df = pd.read_parquet(SRC / name)
        n = len(df)
        half = n // 2
        stem = name.replace(".parquet", "")
        for i, part in enumerate((df.iloc[:half], df.iloc[half:]), 1):
            out = DST / f"{stem}_part{i}.parquet"
            part.to_parquet(out, index=False)
            mb = out.stat().st_size / 1e6
            print(f"{out.name}: {len(part)} rows, {mb:.1f}MB")
