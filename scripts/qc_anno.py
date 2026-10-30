"""标注批次质检：存在性 / JSON 合法 / 条数 / 字段 / 枚举合法性 / id 与输入一致。

用法：python qc_anno.py 2019
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
HIER = {"L0", "L1", "L2", "L3"}


def qc(year: int):
    d_in, d_out = BASE / "anno_input" / str(year), BASE / "anno_output" / str(year)
    meta = json.loads((d_in / "meta.json").read_text("utf-8"))
    bad, ok_n, rows = [], 0, []
    for k in range(meta["n_batches"]):
        b = f"batch_{k:03d}"
        fin, fout = d_in / f"{b}.csv", d_out / f"{b}.json"
        want = set(pd.read_csv(fin, encoding="utf-8-sig")["id"].tolist())
        if not fout.exists():
            bad.append((b, "缺失"))
            continue
        try:
            arr = json.loads(fout.read_text(encoding="utf-8-sig"))
        except Exception as e:
            bad.append((b, f"JSON坏: {str(e)[:40]}"))
            continue
        if not isinstance(arr, list) or len(arr) != len(want):
            bad.append((b, f"条数 {len(arr) if isinstance(arr,list) else '非数组'} != {len(want)}"))
            continue
        prob = []
        for x in arr:
            if not all(key in x for key in REQ):
                prob.append("缺字段")
            elif x["hierarchy"] not in HIER or x["module"] not in MODS:
                prob.append("枚举越界")
        got = set(x.get("id") for x in arr)
        if got != want:
            prob.append(f"id不符(缺{len(want-got)}/多{len(got-want)})")
        if prob:
            bad.append((b, ";".join(sorted(set(prob)))[:60]))
            continue
        ok_n += 1
        rows.extend(arr)
    df = pd.DataFrame(rows).drop_duplicates("id")
    print(f"[{year}] 合格批次 {ok_n}/{meta['n_batches']}；标注任务 {len(df)}/{meta['n_tasks']} "
          f"= {len(df)/meta['n_tasks']:.1%}")
    if bad:
        print("问题批次：")
        for b, why in bad:
            print(f"  {b}: {why}")
    return df, bad


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    qc(int(sys.argv[1]) if len(sys.argv) > 1 else 2019)
