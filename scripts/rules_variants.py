"""规则族锦标赛：在覆盖子图上比较 (a)/(b) 的多种公式化，LLM 属性 vs 词表属性。

同一候选子图上评估，避免属性源与样本混淆。
用法：python rules_variants.py 2019 llm|lex
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from jtagent import evaluate, features
from jtagent.attrs import load_attrs

OUT = Path(r"D:\harness office\research\jobtask-agent\out")
sys.stdout.reconfigure(encoding="utf-8")


def stamp(df, attrs):
    a = attrs.set_index("task")
    df = df.copy()
    for col in ("E_ord", "ctx", "codable", "module", "hierarchy", "ctx_llm"):
        if col in a.columns:
            df[f"{col}_i"] = a[col].reindex(df["ti"]).to_numpy()
            df[f"{col}_j"] = a[col].reindex(df["tj"]).to_numpy()
    df["E_gap"] = (df["E_ord_i"] - df["E_ord_j"]).abs()
    lo = df["E_ord_i"] <= df["E_ord_j"]
    df["ctx_low"] = df["ctx_i"].where(lo, df["ctx_j"])
    df["cod_low"] = df["codable_i"].where(lo, df["codable_j"])
    df["cod_hi"] = df["codable_i"].where(~lo, df["codable_j"])
    df["cod_geom"] = np.sqrt(df["codable_i"].clip(0) * df["codable_j"].clip(0))
    df["same_mod"] = (df["module_i"] == df["module_j"]).astype(float)
    if "hierarchy_i" in df:
        df["same_hier"] = (df["hierarchy_i"] == df["hierarchy_j"]).astype(float)
        df["hier_adj"] = ((df["hierarchy_i"].str[1:].astype(float) -
                           df["hierarchy_j"].str[1:].astype(float)).abs() == 1).astype(float)
    df["coh"] = 0.5 + 0.5 * df["jaccard"]
    df["mix2"] = (df["E_gap"] == 2).astype(float)
    df["sameE"] = (df["E_gap"] == 0).astype(float)
    return df


VARIANTS = {
    "A1 = gap×ctx_low": lambda d: d["E_gap"] / 2 * d["ctx_low"],
    "A2 = 1[E2×E0]×ctx_low": lambda d: d["mix2"] * d["ctx_low"],
    "A3 = gap×ctx×(1-cod)": lambda d: d["E_gap"] / 2 * d["ctx_low"] * (1 - d["cod_low"]),
    "A4 = 1[E2×E0]×ctx×(1-cod)": lambda d: d["mix2"] * d["ctx_low"] * (1 - d["cod_low"]),
    "A5 = gap×ctx_low×cod_hi": lambda d: d["E_gap"] / 2 * d["ctx_low"] * d["cod_hi"],
    "B1 = mod×hom×cod×coh": lambda d: d["same_mod"] * (1 - d["E_gap"] / 2) * d["cod_geom"] * d["coh"],
    "B2 = mod×hier×cod×coh": lambda d: d["same_mod"] * d.get("same_hier", 1.0) * d["cod_geom"] * d["coh"],
    "B3 = mod×hom×cod": lambda d: d["same_mod"] * (1 - d["E_gap"] / 2) * d["cod_geom"],
    "B4 = mod×sameE×coh": lambda d: d["same_mod"] * d["sameE"] * d["coh"],
    "B5 = sameE×coh": lambda d: d["sameE"] * d["coh"],
    "B6 = mod×hier_adj×cod": lambda d: d["same_mod"] * d.get("hier_adj", 0.0) * d["cod_geom"],
}


def main(year: int = 2019, mode: str = "llm"):
    df = features.build_pairs_table(year)
    # 统一覆盖掩码：以 LLM 标注覆盖的任务为准（两侧都被标注）
    cov_mask = stamp(df, load_attrs(mode="llm"))
    cov = cov_mask["ctx_llm_i"].notna() & cov_mask["ctx_llm_j"].notna()
    del cov_mask
    attrs = load_attrs(mode=mode)
    d = stamp(df, attrs)
    d = d[cov].copy()
    y = d["y"].to_numpy()
    print(f"[{mode}] 覆盖子图 {len(d):,} 对, positives={int(y.sum()):,}, pos_rate={y.mean():.5f}")
    rows = []
    for name, fn in VARIANTS.items():
        s = pd.Series(fn(d), index=d.index).fillna(0).to_numpy()
        m = evaluate.rank_metrics(y, s, name)
        m["attr"] = mode
        rows.append(m)
    # 基线
    for name, col in [("共邻", "cn"), ("优先连接", "pa"), ("jaccard", "jaccard"),
                      ("持续性", "bind_TM1")]:
        m = evaluate.rank_metrics(y, d[col].to_numpy(), name)
        m["attr"] = mode
        rows.append(m)
    res = pd.DataFrame(rows).sort_values("AUC", ascending=False)
    res.to_csv(OUT / "results" / f"rules_variants_{year}_{mode}.csv", index=False, encoding="utf-8-sig")
    print(res[["score", "AP", "AUC", f"P@{max(int(y.sum()),1)}", "lift@1%"]].to_string(index=False))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2019,
         sys.argv[2] if len(sys.argv) > 2 else "llm")
