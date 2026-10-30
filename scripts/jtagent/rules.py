"""三条再捆绑守则的可计算化打分（df 需含 features.py 生成的列）。

属性源可替换：lexicon（消融基线）或 LLM 标注（主准则）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _ctx_low(df: pd.DataFrame) -> pd.Series:
    """低暴露一端的语境嵌入度。"""
    take_i = df["E_ord_i"] <= df["E_ord_j"]
    return df["ctx_i"].where(take_i, df["ctx_j"])


def score_A(df: pd.DataFrame) -> pd.Series:
    """(a) 互补性再捆绑：E 差距大 × 低端任务语境嵌入。

    理论签名：可编码(E2)任务被吸收后，与难吸收的判断/协调/问责/具身(E0·高ctx)任务新共捆绑。
    """
    mix = df["E_gap"] / 2.0
    return mix * _ctx_low(df)


def score_B(df: pd.DataFrame) -> pd.Series:
    """(b) 层级解绑：同模块×同暴露×可编码×邻域凝聚 → 狭窄均质新组合。

    方向与 (a) 相反：低 E 差距反而加分。
    """
    same_mod = (df["module_i"] == df["module_j"]).astype(float)
    hom = 1.0 - df["E_gap"] / 2.0
    cod = np.sqrt(df["codable_i"].clip(0) * df["codable_j"].clip(0))
    coh = 0.5 + 0.5 * df["jaccard"]
    return same_mod * hom * cod * coh


def score_PERSIST(df: pd.DataFrame) -> pd.Series:
    return df["bind_TM1"]


def score_PA(df: pd.DataFrame) -> pd.Series:
    return np.log1p(df["pa"])  # 对数化避免极端值支配排序


def score_CN(df: pd.DataFrame) -> pd.Series:
    return df["cn"]


def score_JAC(df: pd.DataFrame) -> pd.Series:
    return df["jaccard"]


RULE_SCORES = {"A_互补再捆绑": score_A, "B_层级解绑": score_B}
BASELINE_SCORES = {"持续性": score_PERSIST, "优先连接": score_PA,
                   "共邻": score_CN, "jaccard": score_JAC}


def add_scores(df: pd.DataFrame) -> pd.DataFrame:
    for name, fn in {**RULE_SCORES, **BASELINE_SCORES}.items():
        df[name] = fn(df)
    return df
