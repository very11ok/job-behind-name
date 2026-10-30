"""训练基线 v0.1：滚动年份候选对评分对比（词表属性版，作为消融基线）。

用法：  python run_backtest.py 2018 2025
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from jtagent import evaluate, features, rules

sys.stdout.reconfigure(encoding="utf-8")


def run_year(t: int, target: str = "y") -> pd.DataFrame:
    df = features.build_pairs_table(t)
    df = rules.add_scores(df)
    y = df[target]
    keep = y.notna() & df[[s for s in rules.RULE_SCORES]].notna().all(axis=1)
    df_eval = df.loc[keep]
    names = list(rules.RULE_SCORES) + list(rules.BASELINE_SCORES)
    res = evaluate.eval_frame(df_eval, names, target=target)
    res.insert(0, "T", t)
    return res


def main(year_min: int = 2018, year_max: int = 2025):
    out = Path(r"D:\harness office\research\jobtask-agent\out\results")
    out.mkdir(parents=True, exist_ok=True)
    parts, summ = [], []
    for t in range(year_min, year_max + 1):
        try:
            df = features.build_pairs_table(t)
            summ.append({"T": t, **features.summarize(df)})
            del df
            parts.append(run_year(t))
            print(f"[ok] {t}: {summ[-1]}")
        except Exception as e:
            print(f"[fail] {t}: {e}")
    res = pd.concat(parts)
    res.to_csv(out / "baseline_metrics.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(summ).to_csv(out / "candidate_summary.csv", index=False, encoding="utf-8-sig")
    print(res.to_string(index=False))


if __name__ == "__main__":
    a = int(sys.argv[1]) if len(sys.argv) > 1 else 2018
    b = int(sys.argv[2]) if len(sys.argv) > 2 else 2025
    main(a, b)