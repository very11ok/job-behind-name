"""逐特征消融：三守则语义的增量由哪个特征承载？

在 2018 训 → 2019 测 的 logistic 上，逐个加入 RULE_FEATS，观察 AUC/AP/Brier/lift 变化。
另做 LLM vs 词表 的同特征对比，检验"增量是否来自 LLM 判定"。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).parent))
from jtagent import features, model
from jtagent.attrs import load_attrs

OUT = Path(r"D:\harness office\research\jobtask-agent\out")
sys.stdout.reconfigure(encoding="utf-8")


def _stamp(df, attrs):
    a = attrs.set_index("task")
    df = df.copy()
    for col in ("E_ord", "ctx", "codable", "module", "hierarchy", "ctx_llm"):
        if col not in a.columns:
            continue
        df[f"{col}_i"] = a[col].reindex(df["ti"]).to_numpy()
        df[f"{col}_j"] = a[col].reindex(df["tj"]).to_numpy()
    df["E_gap"] = (df["E_ord_i"] - df["E_ord_j"]).abs()
    return df


def run(year: int = 2019, mode: str = "llm"):
    tr = _stamp(features.build_pairs_table(year - 1), load_attrs(mode=mode))
    te = _stamp(features.build_pairs_table(year), load_attrs(mode=mode))
    if mode == "llm":
        m_tr = _stamp(features.build_pairs_table(year - 1), load_attrs(mode="llm"))
        m_te = _stamp(features.build_pairs_table(year), load_attrs(mode="llm"))
        tr = tr[(m_tr["ctx_llm_i"].notna() & m_tr["ctx_llm_j"].notna()).to_numpy()]
        te = te[(m_te["ctx_llm_i"].notna() & m_te["ctx_llm_j"].notna()).to_numpy()]
    trp, tep = model._prep(tr), model._prep(te)
    y = tep["y"].to_numpy()
    rows = [{"feats": "纯图基线", **model._metrics(y, _fit(trp, tep, model.BASE_FEATS))}]
    for f in model.RULE_FEATS:
        rows.append({"feats": f"+ {f}", **model._metrics(y, _fit(trp, tep, model.BASE_FEATS + [f]))})
    rows.append({"feats": "+ 全部语义", **model._metrics(y, _fit(trp, tep, model.BASE_FEATS + model.RULE_FEATS))})
    res = pd.DataFrame(rows)
    res["attr"] = mode
    res.to_csv(OUT / "results" / f"ablation_feats_{year}_{mode}.csv", index=False, encoding="utf-8-sig")
    print(f"=== {mode} ===")
    print(res.to_string(index=False))
    return res


def _fit(trp, tep, feats):
    lr = LogisticRegression(C=0.5, max_iter=1000)
    lr.fit(trp[feats].fillna(0).to_numpy(), trp["y"].to_numpy())
    return lr.predict_proba(tep[feats].fillna(0).to_numpy())[:, 1]


if __name__ == "__main__":
    run(2019, "llm")
    run(2019, "lex")
