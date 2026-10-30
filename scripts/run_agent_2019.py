"""标注就绪后的主回测：T=2019→2020，LLM 语义准则 vs 词表 vs 纯图基线。

产出：
  out/results/agent_metrics_2019.csv    三守则(lex/llm) + baseline 的 AP/AUC/P@k/lift
  out/results/clash_2019.csv            logistic 消融对撞（2018 训, 2019 测）
  out/results/agent_preds_2019_sample.parquet  高分候选样例（供 LLM 配送 why）
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from jtagent import evaluate, features, model, rules
from jtagent.attrs import load_attrs

OUT = Path(r"D:\harness office\research\jobtask-agent\out")
sys.stdout.reconfigure(encoding="utf-8")


def _score(df: pd.DataFrame) -> pd.DataFrame:
    df = rules.add_scores(df)  # lexicon 版
    return df


def _stamp(df: pd.DataFrame, attrs: pd.DataFrame) -> pd.DataFrame:
    """把属性列重刷到候选对表上（避免缓存混淆不同属性源）。"""
    a = attrs.set_index("task")
    df = df.copy()
    for col in ("E_ord", "ctx", "codable", "module", "hierarchy", "ctx_llm"):
        if col not in a.columns:
            continue
        df[f"{col}_i"] = a[col].reindex(df["ti"]).to_numpy()
        df[f"{col}_j"] = a[col].reindex(df["tj"]).to_numpy()
    df["E_gap"] = (df["E_ord_i"] - df["E_ord_j"]).abs()
    return df


def main(year: int = 2019, mode: str = "merge", covered_only: bool = False):
    if mode == "llm":
        covered_only = True
    # 1) 读取缓存的候选对 + 用指定属性源重刷
    df_cache = features.build_pairs_table(year)
    attrs_llm = load_attrs(mode=mode)
    df_llm = _stamp(df_cache, attrs_llm)
    mask = df_llm["ctx_i"].notna() & df_llm["ctx_j"].notna() if covered_only \
        else pd.Series(True, index=df_llm.index)
    if covered_only:
        before = len(df_llm)
        df_llm = df_llm[mask].copy()
        print(f"[covered-only] 覆盖子图: {len(df_llm):,}/{before:,} 对 = "
              f"{len(df_llm)/max(before,1):.1%}; 覆盖内 y=1 率 {df_llm['y'].mean():.4f}")
    print(f"[{year}] candidates={len(df_llm):,} positives={int(df_llm['y'].sum()):,} "
          f"y_new={int(df_llm['y_new'].sum()):,}")
    print("attr_src 分布:", attrs_llm["attr_src"].value_counts().to_dict())

    df_llm = _score(df_llm)
    names = list(rules.RULE_SCORES) + list(rules.BASELINE_SCORES)
    res_llm = evaluate.eval_frame(df_llm, names, target="y")
    res_llm["attr"] = {"llm": "LLM三守则", "merge": "llm+lex合并", "lex": "lex"}[mode] + \
                      ("(覆盖子图)" if covered_only else "")

    # 2) 词表纯消融（同覆盖子集）
    df_lex = _stamp(df_cache, load_attrs(mode="lex"))
    if covered_only:
        df_lex = df_lex[mask].copy()
    df_lex = _score(df_lex)
    res_lex = evaluate.eval_frame(df_lex, names, target="y")
    res_lex["attr"] = "lex消融"

    res = pd.concat([res_llm, res_lex])
    res.to_csv(OUT / "results" / f"agent_metrics_{year}.csv", index=False, encoding="utf-8-sig")
    print(res.to_string(index=False))

    # 3) logistic 对撞：T-1 训、T 测。三行 = 纯图 / +词表语义 / +LLM语义（同一覆盖子集）
    try:
        def _frames(mode: str):
            tr = _stamp(features.build_pairs_table(year - 1), load_attrs(mode=mode))
            te = _stamp(features.build_pairs_table(year), load_attrs(mode=mode))
            if covered_only:
                m_tr = _stamp(features.build_pairs_table(year - 1), load_attrs(mode="llm"))
                m_te = _stamp(features.build_pairs_table(year), load_attrs(mode="llm"))
                tr = tr[(m_tr["ctx_llm_i"].notna() & m_tr["ctx_llm_j"].notna()).to_numpy()].copy()
                te = te[(m_te["ctx_llm_i"].notna() & m_te["ctx_llm_j"].notna()).to_numpy()].copy()
            return tr, te

        rows = []
        tr_l, te_l = _frames("lex")
        rows.append(model.clash_one(tr_l, te_l, False, "纯图+持续"))
        if covered_only:
            tr_i, te_i = _frames("llm")
            rows.append(model.clash_one(tr_i, te_i, True, "+LLM三守则语义"))
            rows.append(model.clash_one(tr_l, te_l, True, "+词表语义(对照)"))
        else:
            rows.append(model.clash_one(tr_l, te_l, True, "+三守则语义(词表)"))
        clash = pd.DataFrame(rows)
        clash.to_csv(OUT / "results" / f"clash_{year}.csv", index=False, encoding="utf-8-sig")
        print(clash.to_string(index=False))
    except Exception as e:
        print("clash 失败:", repr(e))

    # 4) 高分样例（供 LLM 机制判别与 why 输出）
    samp = pd.concat([
        df_llm.nlargest(300, "A_互补再捆绑").assign(tag="topA"),
        df_llm.nlargest(300, "B_层级解绑").assign(tag="topB"),
        df_llm.nlargest(300, "共邻").assign(tag="topCN"),
        df_llm.sample(600, random_state=1).assign(tag="random"),
    ]).drop_duplicates(subset=["ti", "tj", "tag"])
    texts = attrs_llm.set_index("task")["task_text"]
    samp["text_i"] = texts.reindex(samp["ti"]).to_numpy()
    samp["text_j"] = texts.reindex(samp["tj"]).to_numpy()
    samp.to_parquet(OUT / "results" / f"agent_preds_{year}_sample.parquet", index=False)
    print("样例:", samp.shape, "y=1 占比:", round(samp["y"].mean(), 3))


if __name__ == "__main__":
    _y = int(sys.argv[1]) if len(sys.argv) > 1 else 2019
    _mode = sys.argv[2] if len(sys.argv) > 2 else "merge"
    _cov = len(sys.argv) > 3 and sys.argv[3] == "covered"
    main(_y, _mode, _cov)
