"""生成三准则 LLM 前因判定批次输入。

每批次一个文本文件 out/judge_input/{rule}_batch_{XX}.txt：
  头部 = 判定协议（前因定义 + 输出格式），正文 = 逐对象渲染块。
对齐键：g1=job, g2=seed, g3=firm（与 labels_g*_2020.parquet 一致）。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

BASE = Path(r"D:\harness office\research\jobtask-agent")
OBJ = BASE / "out" / "objects"
JI = BASE / "out" / "judge_input"
YEAR = 2020
BATCH = 60

PROTO = {
    "g1": """【判定协议 · 准则(a) 互补性再捆绑 —— 前因判定】
单元：一个岗位的任务集合（T=2020 快照）。
前因定义：集合内同时包含——
  ①「AI 可吸收的高暴露可编码任务」：暴露 E2、codability（可编码度）高，纯信息处理、规则明确；
  ②「难被吸收的语境嵌入任务」：依赖判断(judge)/协调(coordinate)/问责(accountable)/具身情境，
     codability 低、暴露 E0/E1。
两类任务并存（①②都出现）才算前因成立 holds=1；只有一类或两类都弱则 holds=0。
p 的含义：给定 2020 年信息，你估计该岗位在 2021-2023 年出现「新任务组合且为高-低暴露搭配」的概率。
""",  # noqa: RUF001
    "g2": """【判定协议 · 准则(b) 层级解绑 —— 前因判定】
单元：一个任务团（任务投影层上以某核心任务为中心的强邻域，T=2020）。
前因定义：团内任务满足——
  ① 同层级：hierarchy（L0例行执行/L1标准解题/L2跨职能协调/L3战略判断）高度集中；
  ② 可编码为主：codability（可编码度）总体高，多数任务规则明确；
  ③ 功能凝聚：模块集中，任务性质均质——整团可被"知识下沉"切进更窄的新岗位。
三点基本满足 holds=1；层级混杂或大量语境嵌入任务则 holds=0。
p 的含义：给定 2020 年信息，你估计该团在 2021-2023 年「分裂为 ≥2 个更窄岗位、分别承载团的一部分」的概率。
""",  # noqa: RUF001
    "g3": """【判定协议 · 准则(c) 模仿性模板扩散 —— 前因判定】
单元：一家企业 × 2020 的岗位结构。
前因定义：该企业的岗位结构存在「模板残留」——表面相似度 surf_sim 明显高于结构相似度
（struct_sim=与自身既往岗位结构相似，xfirm_sim=跨企业任务结构相似）：
  即该企业岗位像流行模板，像的是【措辞】而不是【任务结构】——结构上并不真的同构，
  说明职责措辞是从外部模板复制来的，任务结构尚未跟进。
判断时对比三个数值：surf_sim 相对 struct_sim/xfirm_sim 的残差越大，模板残留越明显，越倾向 holds=1；
三个数值接近（措辞相似可被结构相似解释）则 holds=0。辅以企业规模与功能多样性背景判断。
p 的含义：给定 2020 年信息，你估计该企业 2021-2023 年「新增岗位中模板采纳占比高于全网中位数」的概率。
""",  # noqa: RUF001
}

OUT_FMT = """
【输出】严格 JSON 数组，每个元素对应输入中一个对象块，顺序一致，不输出任何其他文字：
[{"id":"<对象id>","holds":<0|1>,"p":<0..1>,"why":"<≤30字中文依据>"}]
- id 照抄对象块第一行方括号里的 id。
- p 给档位即可：0.05（几乎不可能）/0.1/0.2/0.3/0.5/0.7/0.9。
"""


def _td() -> pd.DataFrame:
    td = pd.read_parquet(BASE / "out" / "snapshots" / "task_dict.parquet")
    td["task"] = td["task"].astype(int)
    texts = td.set_index("task")["task_text"].astype(str)
    return texts


def _trim(s: str, n: int = 90) -> str:
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


def render_g1(texts) -> pd.DataFrame:
    df = pd.read_parquet(OBJ / f"g1_jobs_{YEAR}.parquet")
    blocks = []
    for _, r in df.iterrows():
        ts = [int(x) for x in str(r["tasks"]).split(";")]
        e = str(r["e_ord"]).split(",")
        cod = str(r["cod"]).split(",")
        ctx = str(r["ctx"]).split(",")
        mod = str(r["mod"]).split("|")
        lines = []
        for i, t in enumerate(ts):
            e_lab = {"0": "E0低", "1": "E1中", "2": "E2高"}.get(e[i].strip(), e[i])
            lines.append(f"  t{t} | {_trim(texts.get(t, '?'))} | {e_lab} | "
                         f"可编码{cod[i]} 语境{ctx[i]} | {mod[i] if i < len(mod) else '?'}")
        blocks.append(f"[id={r['job']} | 岗位任务集 {len(ts)} 任务 | 功能模块数 {r['n_mod']}]\n"
                      + "\n".join(lines))
    return pd.DataFrame({"id": df["job"].astype(str), "block": blocks})


def render_g2(texts) -> pd.DataFrame:
    df = pd.read_parquet(OBJ / f"g2_comm_{YEAR}.parquet")
    blocks = []
    for _, r in df.iterrows():
        ts = [int(x) for x in str(r["tasks"]).split(";")]
        e = str(r["e_ord"]).split(",")
        cod = str(r["cod"]).split(",")
        hier = str(r["hier"]).split("|")
        mod = str(r["mod"]).split("|")
        lines = []
        for i, t in enumerate(ts):
            e_lab = {"0": "E0低", "1": "E1中", "2": "E2高"}.get(e[i].strip(), e[i])
            lines.append(f"  t{t} | {_trim(texts.get(t, '?'))} | {e_lab} | "
                         f"可编码{cod[i]} | {hier[i] if i < len(hier) else '?'} | "
                         f"{mod[i] if i < len(mod) else '?'}")
        blocks.append(f"[id={r['seed']} | 任务团 {len(ts)} 任务 | E2占比 {r['e2_share']:.2f} | "
                      f"层级数 {r['hier_n']} | 模块数 {r['n_mod']}]\n" + "\n".join(lines))
    return pd.DataFrame({"id": df["seed"].astype(str), "block": blocks})


def render_g3(texts) -> pd.DataFrame:
    df = pd.read_parquet(OBJ / f"g3_firms_{YEAR}.parquet")
    blocks = []
    for _, r in df.iterrows():
        resid = float(r["surf_sim"]) - max(float(r["struct_sim"]), float(r["xfirm_sim"]))
        blocks.append(
            f"[id={r['firm']} | 企业岗位结构 2020]\n"
            f"  岗位数 {r['n_jobs']} | 平均任务集 {r['mean_size']:.1f} 任务 | 功能模块数 {r['n_mod']}"
            f" | 高暴露E2任务占比 {r['e2_share']:.2f}\n"
            f"  结构相似度(自身既往) struct_sim={r['struct_sim']:.3f}"
            f" | 跨企业结构相似 xfirm_sim={r['xfirm_sim']:.3f}"
            f" | 表面文本相似 surf_sim={r['surf_sim']:.3f}"
            f" | 残差 surf-结构={resid:+.3f}")
    return pd.DataFrame({"id": df["firm"].astype(str), "block": blocks})


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    JI.mkdir(parents=True, exist_ok=True)
    texts = _td()
    total_batches = 0
    for rule, fn in (("g1", render_g1), ("g2", render_g2), ("g3", render_g3)):
        df = fn(texts)
        header = PROTO[rule] + OUT_FMT
        n = 0
        for i in range(0, len(df), BATCH):
            part = df.iloc[i : i + BATCH]
            body = header + "\n".join(part["block"])
            (JI / f"{rule}_batch_{n:03d}.txt").write_text(body, encoding="utf-8")
            n += 1
        total_batches += n
        print(f"{rule}: {len(df)} 对象 → {n} 批（每批≤{BATCH}）")
    print(f"合计 {total_batches} 批 → {JI}")


if __name__ == "__main__":
    main()
